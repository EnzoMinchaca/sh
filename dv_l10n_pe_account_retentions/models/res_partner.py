from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    l10n_pe_is_retention_agent = fields.Boolean(
        string='Es agente de retención?')
