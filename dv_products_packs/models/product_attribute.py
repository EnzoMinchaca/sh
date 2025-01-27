from odoo import api, fields, models

class ProductAttributeStock(models.Model):
    _inherit = "product.attribute"
    
    boolean_stock = fields.Boolean('Stock')
    

class ProductAttributeValueStock(models.Model):
    _inherit = 'product.attribute.value'
    
    stock = fields.Float('Stock', store=True)
    
    
    