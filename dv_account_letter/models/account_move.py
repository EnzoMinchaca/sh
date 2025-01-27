# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from collections import defaultdict
from odoo.exceptions import UserError, ValidationError, AccessError, RedirectWarning
from odoo.tools import (
    date_utils,
    email_re,
    email_split,
    float_compare,
    float_is_zero,
    float_repr,
    format_amount,
    format_date,
    formatLang,
    frozendict,
    get_lang,
    groupby,
    index_exists,
    is_html_empty,
)

class AccountMove(models.Model):
    _inherit = 'account.move'

    redeemed_state = fields.Selection(
        string='Estado de canje',
        selection=[
            ('not_redeemed', 'No canjeado'),
            ('redeemed', 'Canjeado'),
        ],
        default='not_redeemed',
        copy=False,
    )
    letter_id = fields.Many2one(
        'account.letter',
        string='Canje',
        copy=False,
    )
    letter_line_id = fields.Many2one(
        'account.letter.line',
        string='Letra',
        copy=False,
    )

    invoice_payments_widget = fields.Binary(
        groups="account.group_account_invoice,account.group_account_readonly,dv_account_letter.group_tesorery",
        compute='_compute_payments_widget_reconciled_info',
        exportable=False,
        copy=False,
    )
    
    #Herencia de confirmar factura
    def action_post(self):
        res = super(AccountMove, self).action_post()
        if self.letter_line_id and self.l10n_latam_document_type_id.name in ['Nota de Débito', 'Nota de Débito Boleta']:
            #Busca en account.charge.invoice si existe un account.move.line con el nombre de la letra
            charge_invoice = self.env['account.charge.invoices'].search([
                ('move_line_id.name', '=', self.letter_line_id.name),
                ('letter_id.state', '!=', 'cancel')])
            if charge_invoice:
                #Busca el canje no cancelado que tenga en invoice_line_ids el id de charge_invoice
                letter = self.env['account.letter'].search([
                    ('invoice_line_ids', 'in', charge_invoice.id),
                    ('state', '!=', 'cancel')])
            #Agregar la cuenta por cobrar o pagar a invoice_line_ids del canje
            letter.write({
                'invoice_line_ids': [(0, 0, {
                    'document_type_id': self.l10n_latam_document_type_id.id,
                    'move_line_id': self.line_ids.filtered(lambda line: line.account_id.account_type in ['asset_receivable', 'liability_payable']).id,
                    'amount_total_signed': self.amount_total,
                })],
                'debit_notes_ids': [(4, self.id)]
            })
            # return {
            #     'name': 'Letra Protestada',
            #     'view_mode': 'form',
            #     'res_id': letter.id,
            #     'res_model': 'account.letter',
            #     'type': 'ir.actions.act_window',
            #     'target': 'current',
            # }
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
                'move_line_id': invoice.line_ids.filtered(lambda line: line.account_id.account_type in ['asset_receivable', 'liability_payable']).id,
                'amount_total_signed': round(invoice.amount_residual, precision),
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
    
    def _post(self, soft=True):
        user = self.env.user
        account_group = user.has_group('account.group_account_invoice')
        letter_group = user.has_group('dv_account_letter.group_tesorery')
        if letter_group:
            # Si no pertenece, asignarlo temporalmente
            if not account_group:
                nuevo_grupo = self.env.ref('account.group_account_invoice')
                nuevo_grupo.sudo().write({'users': [(4, user.id)]})

            # Llamar al método original
            res = super(AccountMove, self)._post(soft=soft)

            # Si el usuario fue temporalmente asignado, removerlo del grupo
            if not account_group:
                nuevo_grupo.sudo().write({'users': [(3, user.id)]})
        else:
            res = super(AccountMove, self)._post(soft=soft)
        return res
    
    @api.depends('amount_residual', 'move_type', 'state', 'company_id')
    def _compute_payment_state(self):
        super(AccountMove, self)._compute_payment_state()
        #Variante para letras
        for move in self:
            if move.amount_residual == 0 and move.redeemed_state == 'redeemed':
                #Busca los pagos relacionados a las facturas
                payments = move._get_reconciled_payments()
                #Si hay pagos relacionados
                if payments:
                    #Verifica si hay pagos no conciliados con el extracto
                    unreconciled_payments = payments.filtered(lambda payment: not payment.is_total_reconcile_extracted)
                    #Si hay pagos no conciliados
                    if unreconciled_payments:
                        move.payment_state = 'in_payment'
                    else:
                        move.payment_state = 'paid'
                else:
                    move.payment_state = 'paid'