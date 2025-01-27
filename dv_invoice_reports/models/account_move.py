from odoo import fields, models, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    vendedor = fields.Many2one('res.users', string='Vendedor', compute='_compute_vendedor', store=True)

    @api.depends('invoice_origin')
    def _compute_vendedor(self):
        for move in self:
            vendedor = False
            if move.invoice_origin:
                sale_order = self.env['sale.order'].search([('name', '=', move.invoice_origin)], limit=1)
                vendedor = sale_order.user_id if sale_order else False
            move.vendedor = vendedor