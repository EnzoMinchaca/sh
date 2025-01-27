# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pricelist_ = fields.Float(string="Precio de Venta", compute="_compute_pricelist", store=False)
    currency_usd_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.ref('base.USD'),
        string="Moneda USD"
    )

    def _compute_pricelist(self):
        for template in self:
            pricelist = self.env['product.pricelist'].search([('name', '=', 'Dolares')])

            if pricelist:
                # Obtener el precio según la lista de precios seleccionada
                pricelist_items = self.env['product.pricelist.item'].search([
                    ('product_tmpl_id', '=', template.id),
                    ('pricelist_id', '=', pricelist.id),
                ], limit=1)
                if pricelist_items:
                    currency_usd = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
                    price = pricelist._get_product_price(template, 1.0, currency=currency_usd)
                    template.pricelist_ = price
                else:
                    template.pricelist_ = 0.0
            else:
                template.pricelist_ = 0.0


    def action_add_products_to_order(self):
        
        sale_order_id = self.env.context.get('default_sale_order_id')
        sale_order = self.env['sale.order'].browse(sale_order_id)

        if not sale_order:
            return

        # Obtener la lista de precios de la orden de venta
        order_pricelist = sale_order.pricelist_id
        
        # Agregar productos seleccionados a las líneas del pedido
        lines = []
        for product in self:
            
            # Buscar el producto relacionado con el template
            product_product = self.env['product.product'].search([('product_tmpl_id', '=', product.id)], limit=1)

            # Crear una línea de orden temporal
            line = self.env['sale.order.line'].new({
                'order_id': sale_order.id,
                'product_id': product_product.id,
                'product_uom_qty': 1.0,
            })

            # Obtener el precio del producto según la lista de precios predeterminada (en dólares)
            default_pricelist_price = product.pricelist_ if product.pricelist_ else 0.0

            line.price_unit = default_pricelist_price

            # Verificar si la lista de precios de la orden es "Dolares"
            if order_pricelist and order_pricelist.name != 'Dolares':
                # Aplicar la conversión de la lista de precios de la orden
                converted_price = order_pricelist._get_product_price(product_product, 1.0, order_pricelist.currency_id)
            else:
                # Si la lista de precios es "Dolares", usar el precio predeterminado
                converted_price = default_pricelist_price

            # Ajustar solo el precio con el valor calculado en pricelist_
            line.price_unit = converted_price

            # Convertir la línea temporal a un diccionario y añadirla a las líneas de orden
            lines.append((0, 0, line._convert_to_write(line._cache)))
        
        sale_order.write({
            'order_line': lines
        })

    def action_add_products_to_purchase(self):
        purchase_order_id = self.env.context.get('default_purchase_order_id')
        purchase_order = self.env['purchase.order'].browse(purchase_order_id)

        if not purchase_order:
            return

        # Obtener la divisa de la orden de compra
        purchase_currency = purchase_order.currency_id
        
        # Agregar productos seleccionados a las líneas del pedido
        lines = []
        for product in self:
            _logger.info("purchase curreee")
            _logger.info(purchase_currency.name)
            _logger.info("cost curreeee")
            _logger.info(product.cost_currency_id.name)
            product_product = self.env['product.product'].search([('product_tmpl_id', '=', product.id)], limit=1)
            
            # Obtener el costo del producto
            cost = product_product.standard_price

            # Obtener la divisa del costo del producto
            product_currency = product.cost_currency_id

            # Convertir el costo a la divisa de la orden de compra si es necesario
            if product_currency != purchase_currency:
                conversion_rate = product_currency._get_conversion_rate(from_currency=product_currency, to_currency=purchase_currency, company=purchase_order.company_id)
                cost = cost * conversion_rate
            
            # Crear una nueva línea de pedido temporal para aprovechar el comportamiento predeterminado de Odoo
            line = self.env['purchase.order.line'].new({
                'order_id': purchase_order.id,
                'product_id': product_product.id,
                'product_qty': 1.0,
                'price_unit': cost,
            })
            
            # Convertir la línea temporal a un diccionario y añadirla a las líneas a escribir
            lines.append((0, 0, line._convert_to_write(line._cache)))
        
        purchase_order.write({
            'order_line': lines
        })