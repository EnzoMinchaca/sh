from odoo import models, fields

class ContactLine(models.Model):
    _name = 'contact.line'
    _description = 'Contact Line'
    
    sequence = fields.Integer(string='Secuencia')
    partner_id = fields.Many2one('res.partner', string='Partner', ondelete='cascade')
    
    # Pagina CONTACTO
    name = fields.Char(string='Nombre', store=True)
    email = fields.Char(string='Email', store=True)
    phone = fields.Char(string='Teléfono', store=True)
    mobile = fields.Char(string='Celular', store=True)
    area = fields.Char(string='Área', store=True)
    funcion = fields.Char(string='Función', store=True)
    comentario = fields.Text(string='Comentario', store=True)
    
    