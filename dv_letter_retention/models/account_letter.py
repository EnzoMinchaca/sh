# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import timedelta, date
from odoo.exceptions import UserError


class AccountLetter(models.Model):
    _inherit = 'account.letter'

    #Metodo para conciliar las facturas relacionadas
    def action_reconcile_related_invoices(self, move_id):
        debit_lines = []
        credit_lines = []
        #Línea por cobrar o por pagar de las facturas, notas de crédito o letras
        for invoice_line in self.invoice_line_ids:   
            credit_lines.extend(invoice_line.move_id.line_ids.filtered(lambda line: line.account_id.id == invoice_line.account_id.id 
                and not line.l10n_pe_is_withholding_line and line.name in [rec.name for rec in move_id.line_ids]))
        #Línea por cobrar o por pagar del asiento del canje
        for move_line in move_id.line_ids:
            if self.type == 'out_invoice':
                debit_lines.extend(move_line.filtered(lambda line: line.account_id.account_type in ['asset_receivable', 'liability_payable'] 
                    and line.amount_currency < 0.0 and line.name in [credit.name for credit in credit_lines]))
            else:
                debit_lines.extend(move_line.filtered(lambda line: line.account_id.account_type in ['asset_receivable', 'liability_payable'] 
                    and line.amount_currency > 0.0 and line.name in [credit.name for credit in credit_lines]))
        # Ordenar por nombre descendente
        debit_lines.sort(key=lambda x: str(x.name), reverse=True)
        credit_lines.sort(key=lambda x: str(x.name), reverse=True)
        #Conciliación de las líneas
        for debit_line, credit_line in zip(debit_lines, credit_lines):
            # res = debit_line + credit_line
            (debit_line + credit_line).reconcile()