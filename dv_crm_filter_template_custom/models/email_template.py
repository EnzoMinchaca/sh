from odoo import models,api,fields

class EmailTemplateInherit(models.Model):

    _inherit = 'mail.template'

    type_lead = fields.Selection(
        string='Tipo de Lead',
        selection=[('gobierno','GOBIERNO'),('privadas','PRIVADAS')],
        help='Tipo de Lead'
    )
