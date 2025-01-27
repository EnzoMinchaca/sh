from odoo import api, fields, models

class ProductTemplateAttributeLine(models.Model):
    _inherit = 'product.template.attribute.line'

    res_product_id = fields.Many2one('product.template', string='Product')