from odoo import models, fields

class ContactLine(models.Model):
    _name = 'ubicacion.line'
    _description = 'Ubicación'
    
    sequence = fields.Integer(string='Secuencia')
    partner_id = fields.Many2one('res.partner', string='Partner', ondelete='cascade')
    
    # Pagina UBICACION
    tipo = fields.Selection([
        ('contact', 'Contacto'),
        ('invoice', 'Dirección de factura'),
        ('delivery', 'Dirección de entrega'),
        ('followup', 'Direcciones de seguimientos'),
        ('other', 'Otra dirección')
    ], string='Tipo', store=True)
    contact_address = fields.Char(string='Dirección', store=True)
    ref = fields.Char(string='Referencia', store=True)
    distrito = fields.Many2one('l10n_pe.res.city.district', string='Distrito', store=True)
    ciudad = fields.Many2one('res.city', string='Ciudad', store=True)
    pais_id = fields.Many2one('res.country', string='País', store=True)
    