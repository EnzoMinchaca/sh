from odoo import api, fields, models, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    l10n_pe_edi_product_class = fields.Char(string='Clase')
    l10n_pe_edi_product_onu_number = fields.Char(string='N ONU')