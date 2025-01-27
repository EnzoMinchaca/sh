from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    custom = fields.Boolean("Custom", store=True)
    static = fields.Boolean("Static", store=True)
    downloadable = fields.Boolean("Downloadable", store=True)

    @api.model
    def create(self, vals):
        self._check_single_true(vals)
        return super().create(vals)

    def write(self, vals):
        self._check_single_true(vals)
        return super().write(vals)

    def _check_single_true(self, vals):
        if vals.get('custom'):
            vals.update({'static': False, 'downloadable': False})
        elif vals.get('static'):
            vals.update({'custom': False, 'downloadable': False})
        elif vals.get('downloadable'):
            vals.update({'custom': False, 'static': False})

    @api.model
    def get_values(self):
        res = super().get_values()
        res.update({
            'custom': self.env['ir.config_parameter'].sudo().get_param('link_invoice_qr_stg.custom') == 'True',
            'static': self.env['ir.config_parameter'].sudo().get_param('link_invoice_qr_stg.static') == 'True',
            'downloadable': self.env['ir.config_parameter'].sudo().get_param('link_invoice_qr_stg.downloadable') == 'True',
        })
        return res

    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param('link_invoice_qr_stg.custom', self.custom)
        self.env['ir.config_parameter'].sudo().set_param('link_invoice_qr_stg.static', self.static)
        self.env['ir.config_parameter'].sudo().set_param('link_invoice_qr_stg.downloadable', self.downloadable)
