from odoo import api, fields, models
from decimal import Decimal, ROUND_DOWN
import logging
_logger = logging.getLogger(__name__)

class Product(models.Model):
    _inherit = 'product.template'
    
    pack_product_ids=fields.Many2many(
        comodel_name='product.template',
        relation='product_pack_rel',
        column1='src_id',
        column2='dest_id',
        string="Paquete de Productos",
        help="Paquete de productos",
        check_company=True, store=True)
    list_price = fields.Float('Precio de venta', compute='_compute_list_price', store=True, readonly=False)
    components = fields.Char('Componentes', compute='_compute_components', store=True)
    qty_available = fields.Float(
        string="Quantity Available",
        compute='_compute_qty_available',
        digits=(16, 4),  # Total 16 dígitos, 4 decimales
        store=False
    )
        
    @api.depends('pack_product_ids')
    def _compute_list_price(self):
        if self.pack_product_ids:
            for product in self:
                product.list_price = sum(product.pack_product_ids.mapped('list_price'))
    
    @api.depends('pack_product_ids')
    def _compute_components(self):
        for product in self:
            if product.pack_product_ids:
                product.attribute_line_ids.unlink()
                # Crear una lista para almacenar los valores de las líneas de atributos
                attribute_lines_data = []
                # Recopilar todos los atributos y sus valores
                for pack_product in product.pack_product_ids:
                    for line in pack_product.attribute_line_ids:
                        attribute_lines_data.append((0, 0, {
                            'product_tmpl_id': product.id,
                            'attribute_id': line.attribute_id.id,
                            'res_product_id': pack_product.id,
                            'value_ids': [(6, 0, line.value_ids.ids)],
                        }))
                        # for attribute_value_line in line.product_template_value_ids:
                        #     attribute_value_line.res_product_id = pack_product.id
                
                # Asignar las líneas de atributos recopiladas al producto
                product.attribute_line_ids = attribute_lines_data
                # product.attribute_line_ids.product_template_value_ids.unlink()

                # Crear un diccionario para búsqueda rápida
                current_attribute_values = self.env['product.template.attribute.value'].search([
                    ('product_tmpl_id', '=', product.id)
                ])
                attribute_value_dict = {(val.attribute_line_id.id, val.product_attribute_value_id.id): val for val in current_attribute_values}

                # Modificar los registros existentes
                for line in product.attribute_line_ids:
                    # Encontrar la línea de atributo correspondiente en los pack_products
                    for pack_product in product.pack_product_ids:
                        if line.res_product_id.id == pack_product.id:
                            for value_line in pack_product.attribute_line_ids:
                                if line.attribute_id.id == value_line.attribute_id.id:
                                    # Verificar si attribute_id coincide y buscar res_product_id en attribute_line_ids
                                    for attribute_line in value_line.product_template_value_ids:
                                        key = (line.id, attribute_line.product_attribute_value_id.id)
                                        if key in attribute_value_dict:
                                            attribute_value_dict[key].price_extra = attribute_line.price_extra
                                            attribute_value_dict[key].res_product_id = line.res_product_id.id
                                        else:
                                            self.env['product.template.attribute.value'].create({
                                                'attribute_line_id': line.id,
                                                'product_attribute_value_id': attribute_line.product_attribute_value_id.id,
                                                'ptav_active': attribute_line.ptav_active,
                                                'price_extra': attribute_line.price_extra,
                                                'color': attribute_line.color,
                                                'res_product_id': line.res_product_id.id,
                                            })

    def _compute_qty_available(self):
        for rec in self:
            total_qty_available = Decimal('0.0000')

            # Iteramos por las variantes del rec
            for product in rec.product_variant_ids:
                # Filtrar movimientos en estado 'done'
                stock_moves = self.env['stock.move.line'].search([
                    ('product_id', '=', product.id),
                    ('state', '=', 'done')  # Filtra solo movimientos confirmados
                ])
                
                # Calcula entradas y salidas basadas en las ubicaciones
                entradas = sum(
                    Decimal(str(move.quantity)) for move in stock_moves
                    if move.picking_code == 'incoming' or move.reference == 'Cantidad de producto actualizada'
                )
                salidas = sum(
                    Decimal(str(move.quantity)) for move in stock_moves
                    if move.picking_code == 'outgoing'
                )

                # Calculamos la cantidad total disponible
                total_qty_available += entradas - salidas

            # Asignamos el stock real calculado con 4 decimales truncados
            rec.qty_available = float(total_qty_available.quantize(Decimal('0.0001'), rounding=ROUND_DOWN))
                