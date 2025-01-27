from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

class CajaSecuencia(models.Model):
    _name = 'caja.secuencia'
    _description = 'Modelo para la secuencia de una caja en base a su periodo'
    _order = 'create_date desc'
    
    name = fields.Char(string="Secuencia", store=True)
    periodo_id = fields.Many2one(
        'caja.periodo',
        string="Periodo",
        required=True,
        domain="[('caja_id', '=', caja_id)]"
    )
    caja_id = fields.Many2one(
        'caja.caja',
        string="Caja",
        required=True
    )
