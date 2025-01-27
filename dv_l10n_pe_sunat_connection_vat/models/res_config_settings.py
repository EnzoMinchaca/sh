from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    api_dni_token = fields.Char('Token' , config_parameter='sunat.api_dni_token')