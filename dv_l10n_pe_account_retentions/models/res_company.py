from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_pe_is_retention_agent = fields.Boolean(
        related='partner_id.l10n_pe_is_retention_agent', readonly=False)
    withholding_account_id = fields.Many2one(
        'account.account', string='Cuenta de retención', domain="[('deprecated', '=', False)]", readonly=False)
