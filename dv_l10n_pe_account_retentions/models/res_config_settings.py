from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    withholding_account_id = fields.Many2one(
        'account.account', related='company_id.withholding_account_id', readonly=False)
