# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_draft(self):
        self = self.with_context(skip_account_move_synchronization=True)
        res = super(AccountPayment, self).action_draft()
        return res
    
    is_total_reconcile_extracted = fields.Boolean(
        'Pago cancelado con extracto bancario',
        copy=False,
        compute='_compute_is_total_reconcile_extracted',
        store=True,
    )
    
    @api.depends('reconciled_statement_line_ids')
    def _compute_is_total_reconcile_extracted(self):
        for payment in self:
            # Si hay líneas de extracto conciliadas, verifica el monto total
            if payment.reconciled_statement_lines_count > 0:
                total_reconciled_amount = sum(payment.reconciled_statement_line_ids.mapped('amount'))
                payment.is_total_reconcile_extracted = abs(total_reconciled_amount) >= abs(payment.amount)
            else:
                payment.is_total_reconcile_extracted = False