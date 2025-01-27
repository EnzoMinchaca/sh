from odoo import api, fields, models, _
from odoo.exceptions import UserError
import re

class SaleOrderInherit(models.Model):
    _inherit = "sale.order"
    
    def action_confirm(self):
        # Llamar al método original para mantener su funcionalidad
        super(SaleOrderInherit, self).action_confirm()
        
        for order in self:
            for line in order.order_line:
                product = line.product_id
                if product.pack_product_ids:
                    for pack_product in product.pack_product_ids:
                        product_name_values = re.findall(r'\((.*?)\)', product.display_name)
                        if product_name_values:
                            # Dividir los valores por coma y eliminar espacios en blanco
                            product_name_values = [value.strip() for value in product_name_values[0].split(',')]
                        if pack_product.attribute_line_ids:
                            product_attribute_line_ids = pack_product.attribute_line_ids
                        # else:
                        #     product_attribute_line_ids = product.attribute_line_ids
                            for attribute_line in product_attribute_line_ids:
                                if attribute_line.attribute_id.boolean_stock:
                                    for value in attribute_line.value_ids:
                                        # Verificar si el value está en producto seleccionado
                                        if value.name in product_name_values:
                                            if value.stock >= line.product_uom_qty * pack_product.uom_id.ratio:
                                                # raise UserError(_("No hay suficiente stock para el producto %s en el paquete.") % pack_product.display_name)
                                                # Restar el stock
                                                value.stock -= line.product_uom_qty * pack_product.uom_id.ratio
        
        # Contar la cantidad de pickings
        picking_count = len(self.picking_ids)

        for picking in self.picking_ids:
            #Modificar la cantidad del producto pack origen
            # for move in picking.move_ids_without_package:
            #     for move_line in move.move_line_ids:
            #         move_line.quantity = move_line.quantity * move.product_uom.ratio
            #     move.product_uom_qty = move.product_uom_qty * move.product_uom.ratio
            #     move.quantity = move.quantity * move.product_uom.ratio
            picking.modified_pack_product_move(picking_count)
            # picking.sale_id = self.id                               
        return True

    def action_cancel(self):
        # Llamar al método original para mantener su funcionalidad
        super(SaleOrderInherit, self).action_cancel()

        for order in self:
            for line in order.order_line:
                product = line.product_id
                if product.pack_product_ids:
                    for pack_product in product.pack_product_ids:
                        
                        product_name_values = re.findall(r'\((.*?)\)', product.display_name)
                        if product_name_values:
                            # Dividir los valores por coma y eliminar espacios en blanco
                            product_name_values = [value.strip() for value in product_name_values[0].split(',')]

                        if pack_product.attribute_line_ids:
                            product_attribute_line_ids = pack_product.attribute_line_ids
                        else:
                            product_attribute_line_ids = product.attribute_line_ids
                        for attribute_line in product_attribute_line_ids:
                            if attribute_line.attribute_id.boolean_stock:
                                for value in attribute_line.value_ids:
                                    # Verificar si el value está en los valores del producto comprado
                                    if value.name in product_name_values:
                                        # Sumar el stock
                                        value.stock += line.product_uom_qty * pack_product.uom_id.ratio
        return super(SaleOrderInherit, self)._action_cancel()
