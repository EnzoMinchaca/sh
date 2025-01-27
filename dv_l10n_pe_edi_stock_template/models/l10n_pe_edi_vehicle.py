from odoo import models, fields, api, _

class L10NPeEdiVehicle(models.Model):
    _inherit = 'l10n_pe_edi.vehicle'
    
    weight = fields.Float(string='Peso', help='Peso del vehículo en toneladas')
    brand = fields.Char(string='Marca', help='Marca del vehículo')
