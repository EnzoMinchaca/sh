# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_reversed_entry = fields.Boolean(
        string='Es reversa',
        compute='_compute_is_reversed_entry',
        store=True)
    
    @api.depends('move_id', 'move_id.reversed_entry_id')
    def _compute_is_reversed_entry(self):
        for line in self:
            if line.move_id.reversed_entry_id:
                original_line = self.env['account.move.line'].search([
                    ('move_id', '=', line.move_id.reversed_entry_id.id),
                    ('account_id', '=', line.account_id.id),
                    ('debit', '=', line.credit),
                    ('credit', '=', line.debit),
                ], limit=1)
                if original_line:
                    line.is_reversed_entry = True
                    line.td_po = original_line.td_po
                    line.td_invoice = original_line.td_invoice
                else:
                    line.is_reversed_entry = False