from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    placa = fields.Char(string='Placa')

    @api.model
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        if order.partner_id and order.placa:
            if not order.partner_id.x_placa:
                order.partner_id.x_placa = order.placa
        return order

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        for order in self:
            if order.partner_id and order.placa:
                if not order.partner_id.x_placa:
                    order.partner_id.x_placa = order.placa
        return res


    @api.onchange('partner_id')
    def _compute_placa(self):
        if self.partner_id and self.partner_id.x_placa:
            self.placa = self.partner_id.x_placa
    
    @api.onchange('placa')
    def _compute_partner(self):
        if self.placa:
            partner = self.env['res.partner'].search([('x_placa', '=', self.placa)], limit=1)
            if partner:
                self.partner_id = partner.id

    def _get_report_base_filename(self):
        res = super()._get_report_base_filename()
        if self.company_id.country_id.code == 'PE' or self.company_id.country_id.code == 'US':
            res = 'dv_customization_formats.report_pe_price_document'
        return res
