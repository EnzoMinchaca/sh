# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountAccount(models.Model):
    _inherit = 'account.account'

    account_analytic_id = fields.Many2one('account.analytic.account', 'SKU')