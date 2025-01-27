# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    #Método para crear un caje de letras
    def create_account_letter(self):
        selected_invoices = self.env['account.move'].browse(self._context.get('active_ids', []))
        if not selected_invoices:
            selected_invoices = self
        partner_ids = set(invoice.partner_id.id for invoice in selected_invoices)
        if len(partner_ids) > 1:
            raise UserError('Las facturas seleccionadas no pertenecen al mismo socio.')
        if any(invoice.payment_state == 'paid' for invoice in selected_invoices):
            raise UserError('Solo se pueden canjear facturas no pagadas totalmente.')
        if any(invoice.state != 'posted' for invoice in selected_invoices):
            raise UserError('Solo se pueden canjear facturas publicadas.')
        precision = selected_invoices[0].currency_id.decimal_places
        letter_vals = {
            'currency_id': selected_invoices[0].currency_id.id,
            'type': selected_invoices[0].move_type,
            'partner_id': selected_invoices[0].partner_id.id,
            'invoice_line_ids': [(0, 0, {
                'document_type_id': invoice.l10n_latam_document_type_id.id,
                'move_line_id': invoice.line_ids.filtered(lambda line: line.account_id.account_type in ['asset_receivable', 'liability_payable']
                    and not line.l10n_pe_is_withholding_line).id,
                'amount_total_signed': round(invoice.amount_residual, precision) - invoice.l10n_pe_withholding_amount,
            }) for invoice in selected_invoices],
        }
        letter = self.env['account.letter'].create(letter_vals)
        return {
            'name': 'Canje de Letra',
            'view_mode': 'form',
            'res_id': letter.id,
            'res_model': 'account.letter',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

