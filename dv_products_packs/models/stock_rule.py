from odoo import models
import logging
from collections import defaultdict, namedtuple

from dateutil.relativedelta import relativedelta

from odoo import SUPERUSER_ID, _, api, fields, models, registry
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_compare, float_is_zero, html_escape
from odoo.tools.misc import split_every

_logger = logging.getLogger(__name__)

class ProcurementException(Exception):
    """An exception raised by ProcurementGroup `run` containing all the faulty
    procurements.
    """
    def __init__(self, procurement_exceptions):
        """:param procurement_exceptions: a list of tuples containing the faulty
        procurement and their error messages
        :type procurement_exceptions: list
        """
        self.procurement_exceptions = procurement_exceptions
        
class StockRuleInherit(models.Model):
    _inherit= 'stock.rule'
    
    @api.model
    def _run_pull(self, procurements):
        moves_values_by_company = defaultdict(list)
        mtso_products_by_locations = defaultdict(list)

        # To handle the `mts_else_mto` procure method, we do a preliminary loop to
        # isolate the products we would need to read the forecasted quantity,
        # in order to to batch the read. We also make a sanitary check on the
        # `location_src_id` field.
        for procurement, rule in procurements:
            if not rule.location_src_id:
                msg = _('No source location defined on stock rule: %s!', rule.name)
                raise ProcurementException([(procurement, msg)])

            if rule.procure_method == 'mts_else_mto':
                mtso_products_by_locations[rule.location_src_id].append(procurement.product_id.id)

        # Get the forecasted quantity for the `mts_else_mto` procurement.
        forecasted_qties_by_loc = {}
        for location, product_ids in mtso_products_by_locations.items():
            products = self.env['product.product'].browse(product_ids).with_context(location=location.id)
            forecasted_qties_by_loc[location] = {product.id: product.free_qty for product in products}

        # Prepare the move values, adapt the `procure_method` if needed.
        procurements = sorted(procurements, key=lambda proc: float_compare(proc[0].product_qty, 0.0, precision_rounding=proc[0].product_uom.rounding) > 0)
        for procurement, rule in procurements:
            procure_method = rule.procure_method
            if rule.procure_method == 'mts_else_mto':
                qty_needed = procurement.product_uom._compute_quantity(procurement.product_qty, procurement.product_id.uom_id)
                if float_compare(qty_needed, 0, precision_rounding=procurement.product_id.uom_id.rounding) <= 0:
                    procure_method = 'make_to_order'
                    for move in procurement.values.get('group_id', self.env['procurement.group']).stock_move_ids:
                        if move.rule_id == rule and float_compare(move.product_uom_qty, 0, precision_rounding=move.product_uom.rounding) > 0:
                            procure_method = move.procure_method
                            break
                    forecasted_qties_by_loc[rule.location_src_id][procurement.product_id.id] -= qty_needed
                elif float_compare(qty_needed, forecasted_qties_by_loc[rule.location_src_id][procurement.product_id.id],
                                   precision_rounding=procurement.product_id.uom_id.rounding) > 0:
                    procure_method = 'make_to_order'
                else:
                    forecasted_qties_by_loc[rule.location_src_id][procurement.product_id.id] -= qty_needed
                    procure_method = 'make_to_stock'

            move_values = rule._get_stock_move_values(*procurement)
            move_values['procure_method'] = procure_method
            moves_values_by_company[procurement.company_id.id].append(move_values)
        
        # Obtener la ubicación de origen y destino de la regla principal
        rule_src_location = rule.location_src_id
        rule_dest_location = rule.location_dest_id

        sale_order_name = procurement.origin
        org_rule = rule.id

        if sale_order_name:
            # Buscar el sale.order relacionado usando el campo name
            sale_order = self.env['sale.order'].search([('name', '=', sale_order_name)], limit=1)

            # Buscar en las líneas de pedido (order_line) aquella que tenga un product_id con pack_product_ids
            sale_line = sale_order.order_line.filtered(lambda line: line.product_id.pack_product_ids)

            if sale_line:
                product_index_map = {}
                product_ids = sale_line.product_id.pack_product_ids

                # Crear un conjunto de nombres de productos para la comparación
                product_names = set(product_id.display_name for product_id in product_ids)
                # Agregar el nombre del producto en sale_line a product_names
                product_names.add(sale_line.product_id.display_name)

                index = 0
                for product_id in product_ids:
                    for route in product_id.route_ids:
                        for product_rule in route.rule_ids:
                            if (product_rule.location_src_id == rule_src_location and
                                    product_rule.location_dest_id == rule_dest_location):
                                product_index_map[index] = product_id.id
                                index += 1
                                break  # Salir del for product_rule si se encuentra coincidencia
                        if index in product_index_map:
                            break  # Salir del for route si se encuentra coincidencia

            # Ahora procesamos moves_values_by_company usando product_index_map
            for company_id, moves_values in moves_values_by_company.items():
                if sale_line:
                    move = moves_values[0]  # Asumimos que moves_values ya está definido en el contexto

                    # Filtrar moves_values para eliminar los movimientos no deseados
                    filtered_moves_values = []
                    for mv in moves_values:
                        # Verificar si el 'name' del movimiento contiene el nombre de algún producto en product_names
                        if any(product_name in mv['name'] for product_name in product_names):
                            filtered_moves_values.append(mv)

                    moves_values = filtered_moves_values
                    
                    # Nueva lista para almacenar los movimientos generados
                    new_moves_values = []

                    # Iterar sobre los índices y productos en product_index_map
                    for idx, product_id in product_index_map.items():
                        product_template = self.env['product.template'].search([('id', '=', product_id)], limit=1)

                        # Crear un nuevo movimiento basado en el movimiento original
                        new_move = move.copy()
                        
                        # Modificar los datos del nuevo movimiento
                        new_move.update({
                            'name': product_template.display_name,
                            'product_id': product_template.product_variant_ids[0].id,
                            'description_picking': product_template.description_picking,
                        })

                        # Agregar el nuevo movimiento a new_moves_values
                        new_moves_values.append(new_move)
                    moves_values = new_moves_values
                # Crear los movimientos con privilegios de superusuario
                moves = self.env['stock.move'].with_user(SUPERUSER_ID).sudo().with_company(company_id).create(moves_values)
                moves._action_confirm()
                break  # Esto se asume que es intencional, si no es necesario, se debería eliminar.
                
        return True
