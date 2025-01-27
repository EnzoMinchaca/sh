from odoo import models, fields, api 

class HelpdeskSla(models.Model):
    _inherit = 'helpdesk.sla'

    tiempo_primera_respuesta = fields.Float(string='Tiempo de Primera Respuesta (horas)')