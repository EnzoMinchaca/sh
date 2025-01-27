from odoo import models, fields, api

class ContactLine(models.Model):
    _name = 'data.line'
    _description = 'Data'
    
    sequence = fields.Integer(string='Secuencia')
    
    # Pagina DATOS
    partner_id = fields.Many2one('res.partner', string='Partner', ondelete='cascade', store=True)
    razon_social = fields.Char(store=True)
    vat = fields.Char(store=True)
    tipo_documento = fields.Many2one(
        'l10n_latam.identification.type',
        string="Tipo de documento",
        default=lambda self: self.env['l10n_latam.identification.type'].search([('name', 'ilike', 'RUC')], limit=1)
    )
    nombre_comercial = fields.Char(string='Nombre Comercial', store=True)
    email = fields.Char(store=True)
    mobile = fields.Char(store=True)
    category_id = fields.Many2many('res.partner.category', string='Etiquetas')
    tipo = fields.Selection([
        ('cliente', 'Cliente'),
        ('proveedor', 'Proveedor'),
        ('externo', 'Externo'),
        ('interno', 'Interno')
    ], string='Tipo', store=True)
    tipo_id = fields.Many2many('contact.types', string='Tipos', compute='compute_data_lines_types', store=True, readonly=False)
    comentario = fields.Text(store=True)
    area = fields.Char(string='Área', store=True)
    funcion = fields.Char(string='Puesto', store=True)

    def create(self, vals_list):
        record = super(ContactLine, self).create(vals_list)
        if record.partner_id.class_type:
            record.tipo = record.partner_id.class_type

    @api.depends('tipo')
    def compute_data_lines_types(self):
        for record in self:
            contact_types = self.env['contact.types']
            if record.tipo == 'cliente':
                record.tipo_id = contact_types.search([('name', 'ilike', 'Cliente')], limit=1)
            elif record.tipo == 'proveedor':
                record.tipo_id = contact_types.search([('name', 'ilike', 'Proveedor')], limit=1)
            elif record.tipo == 'externo':
                record.tipo_id = contact_types.search([('name', 'ilike', 'Externo')], limit=1)
            elif record.tipo == 'interno':
                record.tipo_id = contact_types.search([('name', 'ilike', 'Interno')], limit=1)