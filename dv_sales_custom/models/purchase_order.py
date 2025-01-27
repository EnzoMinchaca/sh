# -*- coding: utf-8 -*-
from odoo import models, fields

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def action_open_product_selector(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Seleccionar Productos',
            'res_model': 'product.template',
            'view_mode': 'tree',
            'view_id': self.env.ref('dv_sales_custom.many_product_tree_view_purchase').id,
            'target': 'current',
            'context': {
                'default_purchase_order_id': self.id
            },
        }