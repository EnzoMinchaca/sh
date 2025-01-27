# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    reconcile_company_child_ids = fields.Many2many(
        'res.company', 
        'company_concile_child_rel',
        'company_id', 
        'child_id'
    )
