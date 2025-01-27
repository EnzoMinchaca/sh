from odoo import models, fields

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def open_wizard_successive_discounts(self):
        self.ensure_one() 

        discount = self.env['sale.successive.discounts'].search([
            ('sale_order_line_id', '=', self.id)
        ], limit=1)

        if not discount:

            discount = self.env['sale.successive.discounts'].create({
                'sale_order_line_id': self.id,
                'original_price': self.price_unit,
                'seller_id': self.order_id.user_id.partner_id.id
            })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Descuentos Sucesivos',
            'res_model': 'sale.successive.discounts',
            'res_id': discount.id,
            'view_mode': 'form',
            'target': 'new',
        }
