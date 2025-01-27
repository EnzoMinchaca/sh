from odoo import models, fields

class ContactLine(models.Model):
    _name = 'accesos.line'
    _description = 'Accesos'
    
    sequence = fields.Integer(string='Secuencia')
    partner_id = fields.Many2one('res.partner', string='Partner', ondelete='cascade')
    
    # Pagina ACCESOS
    nombre_acceso = fields.Char(string='Nombre', store=True)
    link = fields.Char(string='Link', store=True)
    usuario = fields.Char(string='Usuario', store=True)
    clave = fields.Char(string='Clave', store=True)