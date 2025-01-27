# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class dv_account_letter(models.Model):
#     _name = 'dv_account_letter.dv_account_letter'
#     _description = 'dv_account_letter.dv_account_letter'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

