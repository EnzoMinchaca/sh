from odoo import models, fields, api
from odoo.exceptions import UserError

class ResCompany(models.Model):
    _inherit = 'res.company'
    
    # description_bomberos = fields.Text(string="Descripcion Permiso Bomberos", store=True)
    # description_interior = fields.Text(string="Descripcion Permiso Interior", store=True)
    # description_ambiente = fields.Text(string="Descripcion Permiso Ambiente", store=True)
    
    firma_image = fields.Binary(string="Imagen de firma", attachment=True, store=True)
    sello = fields.Binary(string="Imagen de sello", attachment=True, store=True)