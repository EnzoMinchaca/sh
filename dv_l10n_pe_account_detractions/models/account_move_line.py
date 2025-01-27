from odoo import api, fields, models, _

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    l10n_pe_is_spot_line = fields.Boolean(string='Es línea de detracción', compute='_compute_l10n_pe_is_spot_line')
    
    def _compute_l10n_pe_is_spot_line(self):
        for line in self:
            line.l10n_pe_is_spot_line = abs(line.balance) == line.move_id.l10n_pe_spot_amount_currency