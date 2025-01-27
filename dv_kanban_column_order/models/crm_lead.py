# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    order_desc = fields.Boolean(string='Ordenar descendente', related='stage_id.order_desc', store=True)
    order_asc = fields.Boolean(string='Ordenar ascendente', related='stage_id.order_asc', store=True)
    field_by_order = fields.Many2one('ir.model.fields', string='Campo por ordenar', related='stage_id.field_by_order', store=True)
    field_by_order_name = fields.Char(string='Campo por ordenar', related='stage_id.field_by_order_name', store=True)