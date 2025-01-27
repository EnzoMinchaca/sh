from odoo import models, fields

class ContactTypes(models.Model):
    _name = 'contact.types'
    _description = 'Contact Types'
    
    name = fields.Char(string='Nombre Tipo', required=True)