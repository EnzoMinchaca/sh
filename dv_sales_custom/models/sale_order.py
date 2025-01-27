# -*- coding: utf-8 -*-
from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_open_product_selector(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Seleccionar Productos',
            'res_model': 'product.template',
            'view_mode': 'tree',
            'view_id': self.env.ref('dv_sales_custom.many_product_tree_view').id,
            'target': 'current',
            'context': {
                'default_sale_order_id': self.id
            },
        }