from odoo import models, fields, api
from collections import Counter

class PickingTypeInherit(models.Model):
    _inherit = "stock.picking"

    is_cahnge_uom = fields.Boolean(string='Is Change UOM', compute='compute_is_change_uom', store=True)
    
    @api.depends('move_ids_without_package.is_change_uom')
    def compute_is_change_uom(self):
        for record in self:
            if record.move_ids_without_package:
                record.is_cahnge_uom = True
            else:
                record.is_cahnge_uom = False
    #Metodo que modifica los movimientos para el reporte de Albaranes
    def get_move_report_lines(self):
        for record in self:
            actual_lines = record.move_ids_without_package
            for move in record.move_ids_without_package:
                if move.product_id.pack_product_ids:
                    for pack_product in move.product_id.pack_product_ids:
                        out_product = actual_lines.filtered(lambda l: l.product_tmpl_id == pack_product)
                        if out_product:
                            actual_lines -= out_product
            return actual_lines

    #Metodo de valifación de entregas ---> Modificado a button_validate_test para quitar funcionalidad
    def button_validate(self):
        result = super(PickingTypeInherit, self).button_validate()

        # Extraer la orden de venta asociada
        order = self.env['sale.order'].search([('name', '=', self.origin)], limit=1)
        modified_pickings = []

        # if order:
        #     # Recoger todos los pickings relacionados a la orden menos el actual
        #     pickings = order.picking_ids.sorted(lambda p: p.id)
        #     if len(pickings) == 1:
        #         filtered_pickings = pickings
        #         move_line_state = 'done'
        #     else:
        #         filtered_pickings = pickings.filtered(lambda p: p.id != self.id and p.state != 'done')
        #         move_line_state = 'assigned'
        #     for picking in filtered_pickings:
        #         # Filtrar líneas que son packs de productos
        #         for sale_line in order.order_line.filtered(lambda l: l.product_id.pack_product_ids):
        #             # Obtener los templates de productos correspondientes en pack_product_ids
        #             pack_product_templates = sale_line.product_id.pack_product_ids

        #             # Almacenar los productos de los movimientos del picking y contar sus ocurrencias
        #             picking_product_counts = Counter(
        #                 picking.move_ids_without_package.mapped(lambda move: move.product_id.product_tmpl_id)
        #             )

        #             # Comprobar si todos los productos del pack están en los movimientos del picking con la cantidad correcta
        #             all_components_in_picking = all(
        #                 picking_product_counts.get(product_template, 0) >= 1 for product_template in pack_product_templates
        #             )

        #             # Verificar si el pack ya está presente en el picking
        #             pack_already_in_picking = picking.move_ids_without_package.filtered(
        #                 lambda ml: ml.product_id.product_tmpl_id == sale_line.product_id.product_tmpl_id
        #             )

        #             if all_components_in_picking and not pack_already_in_picking:
        #                 # Agregar el pack completo como una línea en el picking
        #                 line_values = {
        #                     'name': sale_line.name,
        #                     'display_name': sale_line.product_id.display_name,
        #                     'product_id': sale_line.product_id.id,
        #                     'location_id': picking.location_id.id,
        #                     'location_dest_id': picking.location_dest_id.id,
        #                     'product_uom_qty': sale_line.product_uom_qty * sale_line.product_id.uom_id.ratio,
        #                     'quantity': sale_line.product_uom_qty * sale_line.product_id.uom_id.ratio,
        #                     'state': move_line_state,
        #                 }
        #                 picking.write({
        #                     'move_ids_without_package': [(0, 0, line_values)],
        #                 })
        #                 modified_pickings.append(picking)
        # Cambiar el estado de los pickings modificados
        if order:
            pickings = order.picking_ids.sorted(lambda p: p.id)
            if pickings and len(pickings) == 1:
                pickings.state = 'done'
            else:
                for picking in pickings.filtered(lambda p: p.id != self.id):
                    previous_pickings = pickings.filtered(lambda p: p.id < picking.id)
                    if previous_pickings:
                        previous_done = all(prev.state == 'done' for prev in previous_pickings)
                        if previous_done:
                            picking.state = 'assigned'
                        # elif self.id < picking.id and all(prev.state == 'done' for prev in pickings.filtered(lambda p: p.id < self.id)):
                        #     picking.state = 'assigned'
                        # else:
                        #     picking.state = 'waiting'
                        
            sale_lines_with_packs = order.order_line.filtered(lambda l: l.product_id.pack_product_ids and l.selected_route_id)
            if sale_lines_with_packs:
                self._remove_duplicate_order_lines(order, sale_lines_with_packs)
            return result
    
    def _remove_duplicate_order_lines(self, order, sale_lines_with_packs):
        order.state = 'draft'
        for line in sale_lines_with_packs:
            if line:
                # Obtener los productos del pack
                pack_products = line.product_id.pack_product_ids.mapped('product_variant_id')
                
                for order_line in order.order_line:
                    # Eliminar la línea si es un producto del pack sin ruta seleccionada
                    if order_line.product_id in pack_products and not order_line.selected_route_id:
                        order_line.unlink()

                    # Controlar si el producto principal del pack se repite sin ruta
                    elif order_line.product_id == line.product_id and not order_line.selected_route_id:
                        order_line.unlink()
                    
                    # Controlar si la variante del producto del pack se repite sin ruta
                    else:
                        for pack_product in pack_products:
                            if order_line.product_id in pack_product.product_variant_ids and not order_line.selected_route_id:
                                order_line.unlink()
        order.state = 'sale'

    #Metodo que modifica los movimientos
    def modified_pack_product_move(self, picking_count):
        #Obtiene la ubicacion de origen y destino
        location_id = self.location_id
        location_dest_id = self.location_dest_id
        #Modifica el estado a borrador
        previous_state = self.state
        # Inicializar un conjunto para almacenar los IDs de líneas de orden ya usadas en todas las iteraciones de move
        used_order_line_ids = set()
        #Obtiene el producto pack de la linea de movimiento
        for move in self.move_ids_without_package:
            new_moves_values = []
            is_first_line = False
            product_id = move.product_id
            sale_order_line = self.env['sale.order.line'].search([
                ('product_id', '=', product_id.id),
                ('order_id.picking_ids', 'in', [self.id]),
                ('id', 'not in', list(used_order_line_ids))  # Excluir líneas ya usadas
            ], limit=1)
            if sale_order_line:
                initial_qty = sale_order_line.product_uom_qty
                uom_id = sale_order_line.product_uom
            else:
                initial_qty = move.product_uom_qty
                uom_id = move.product_uom
            #Flujo para el movimiento con producto pack inicial
            if product_id.pack_product_ids:
                #Obtiene los producto pack
                pack_product = product_id.pack_product_ids
                #Obtiene la regla de la ruta
                for product in pack_product:
                    found_route = False
                    for route in product.route_ids:
                        if found_route:
                            break
                        for product_rule in route.rule_ids:
                            if (product_rule.location_src_id == location_id and product_rule.location_dest_id == location_dest_id):
                                # Filtra las variantes del producto pack
                                pack_variant_values = product_id.product_template_variant_value_ids.filtered(lambda line: line.res_product_id == product)
                                if not pack_variant_values:
                                    selected_product_variant = product.product_variant_ids[0]
                                else:
                                    # Busca el producto variante que coincida en attribute_id y name con las variantes del pack
                                    selected_product_variant = product.product_variant_ids.filtered(
                                        lambda variant: all(
                                            any(
                                                pack_value.attribute_id == variant_value.attribute_id and pack_value.name == variant_value.name
                                                for variant_value in variant.product_template_variant_value_ids
                                            )
                                            for pack_value in pack_variant_values
                                        )
                                    )
                                    if not selected_product_variant:
                                        selected_product_variant = product.product_variant_ids[0]
                                #Crea una copia del movimiento
                                if previous_state == 'assigned':
                                    quantity = initial_qty
                                else:
                                    quantity = 0
                                # Condiciones según el número de pickings y estado
                                if picking_count == 1 or self.state == 'waiting':
                                    for move_line in move.move_line_ids:
                                        previous_state = move_line.state
                                        move_line.state = 'draft'
                                        if move_line.product_id == product_id:
                                            move_line.update({
                                                'product_uom_id': sale_order_line.product_uom.id,
                                                'quantity': quantity * uom_id.ratio,
                                            })
                                        move_line.state = previous_state
                                    #Actualización de valores del producto pack
                                    move.product_uom_qty = initial_qty * uom_id.ratio
                                    # move.quantity = quantity * uom_id.ratio
                                    move.product_uom = uom_id
                                    # No reemplaza el pack, solo agrega al final
                                    move_values = {
                                        'name': product.name,
                                        'display_name': product.display_name,
                                        'product_id': selected_product_variant.id,
                                        'location_id': location_id.id,
                                        'location_dest_id': location_dest_id.id,
                                        'picking_id': self.id,
                                        'product_uom_qty': initial_qty * selected_product_variant.uom_id.ratio,
                                        'quantity': quantity * selected_product_variant.uom_id.ratio,
                                        'description_picking': product.description_picking,
                                    }
                                    new_moves_values.append(move_values)
                                    found_route = True
                                    break
                                else:
                                    if is_first_line == False:
                                        #Ubica y agrega el producto en move_line_ids del producto pack modificado
                                        for move_line in move.move_line_ids:
                                            previous_state = move_line.state
                                            move_line.state = 'draft'
                                            if move_line.product_id == product_id:
                                                move_line.update({
                                                    'product_id': selected_product_variant.id,
                                                    'product_uom_id': selected_product_variant.uom_id.id,
                                                    'quantity': quantity * uom_id.ratio,
                                                })
                                            move_line.state = previous_state
                                        #Reemplaza los valores del producto pack por subproductos
                                        move.update({
                                            'name': product.name,
                                            'display_name': product.display_name,
                                            'product_id': selected_product_variant.id,
                                            'description_picking': product.description_picking,
                                            'product_uom_qty': initial_qty * selected_product_variant.uom_id.ratio,
                                            'product_uom': selected_product_variant.uom_id,
                                        })
                                        
                                        is_first_line = True
                                        found_route = True
                                        break
                                    else:
                                        #Reemplaza los valores del producto pack por subproductos
                                        move_values = {
                                            'name': product.name,
                                            'display_name': product.display_name,
                                            'product_id': selected_product_variant.id,
                                            'location_id': location_id.id,
                                            'location_dest_id': location_dest_id.id,
                                            'picking_id': self.id,
                                            'product_uom_qty': initial_qty * selected_product_variant.uom_id.ratio,
                                            'quantity': quantity * selected_product_variant.uom_id.ratio,
                                            'description_picking': product.description_picking,
                                        }
                                        new_moves_values.append(move_values)
                                        found_route = True
                                        break
                # move.state = 'draft'
                # move.unlink()
                #Crea los nuevos movimientos
                self.env['stock.move'].create(new_moves_values)
                used_order_line_ids.add(sale_order_line.id)
            #Flujo para el movimiento sin producto pack
            else:
                # Verificar si se encontró la línea y usar la UdM de esa línea
                if sale_order_line:
                    # Aplicar la cantidad según la UdM específica de la línea de orden
                    move.product_uom_qty = initial_qty * sale_order_line.product_uom.ratio
                    move.product_uom = sale_order_line.product_uom
                    # Agregar el ID de la línea de orden al conjunto de IDs usados
                    used_order_line_ids.add(sale_order_line.id)
                else:
                    # Si no hay línea de orden, usar la UdM del producto como respaldo
                    move.product_uom_qty = initial_qty * move.product_uom.ratio
        self.state = previous_state