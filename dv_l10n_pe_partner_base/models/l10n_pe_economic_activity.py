from odoo import _, api, fields, models


class L10NPeEconomicActivity(models.Model):
    _name = 'l10n_pe.economic.activity'

    code = fields.Char('Código')
    name = fields.Char('Nombre')
