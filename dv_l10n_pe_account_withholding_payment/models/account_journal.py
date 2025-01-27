from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    l10n_pe_is_withhold_journal = fields.Boolean(string='Es Diario de retención')

    @api.onchange('type')
    def _onchange_journal_type(self):
        # Forzar el tipo de retención a falso si el tipo de diario no es general
        if self.type != 'purchase':
            self.l10n_pe_is_withhold_journal = False
