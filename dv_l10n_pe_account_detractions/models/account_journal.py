from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    l10n_pe_is_spot_bank_journal = fields.Boolean(string='Es Banco de detracción')

    @api.onchange('type')
    def _onchange_spot_type(self):
        # Forzar el valor de l10n_pe_is_spot_bank_journal a False cuando el tipo de diario no es bancario
        if self.type != 'bank':
            self.l10n_pe_is_spot_bank_journal = False
