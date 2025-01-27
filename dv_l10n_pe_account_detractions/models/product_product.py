from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.onchange('l10n_pe_withhold_code')
    def _onchange_l10n_pe_withhold_code(self):
        if self.l10n_pe_withhold_code:
            self.l10n_pe_withhold_percentage = self.env['l10n_pe.spot.code'].search(
                [('code', '=', self.l10n_pe_withhold_code)]).percentage
        else:
            self.l10n_pe_withhold_percentage = 0.0
