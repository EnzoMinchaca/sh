from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    # @api.model
    # def create(self, vals):
    #     record = super(Sale_order, self).create(vals)
    #     followers = [record.partner_id.id, record.user_id.partner_id.id]
    #     followers = list(filter(None, followers))  # Remove any None values
    #     if followers:
    #         record.message_subscribe(partner_ids=followers)
    #     return record

    # def write(self, vals):
    #     res = super(Sale_order, self).write(vals)
    #     for record in self:
    #         followers = [record.partner_id.id, record.user_id.partner_id.id]
    #         followers = list(filter(None, followers))  # Remove any None values
    #         if followers:
    #             record.message_subscribe(partner_ids=followers)
    #     return res