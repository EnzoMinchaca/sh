from odoo import api, fields, models

class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'

    res_product_id = fields.Many2one('product.template', string='Producto Relacionado')
    res_product_name = fields.Char(related='res_product_id.name', string='Referencia de producto')