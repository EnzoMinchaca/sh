from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_placa = fields.Char(string='Placa')
