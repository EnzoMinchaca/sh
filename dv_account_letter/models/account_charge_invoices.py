# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountChargeInvoices(models.Model):
    _name = 'account.charge.invoices'
    _description = 'Carga de Facturas'

    name = fields.Char(
        string='Nombre',
        compute='_compute_name',
    )
    letter_id = fields.Many2one(
        'account.letter',
        string='Letra',
    )
    move_invoice_type = fields.Selection(
        string='Tipo',
        related='letter_id.type',
    )
    document_type_id = fields.Many2one(
        'l10n_latam.document.type',
        string='Tipo de documento',
    )
    move_id = fields.Many2one(
        'account.move',
        related='move_line_id.move_id',
        string='Factura',
    )
    invoice_name = fields.Char(
        string='Nro Comprobante',
        related='move_id.name',
    )
    move_line_name = fields.Char(
        string='Referencia',
        related='move_line_id.name',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Socio',
        related='letter_id.partner_id',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        related='move_id.company_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        related='letter_id.currency_id',
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Diario',
        related='move_id.journal_id',
    )
    account_id = fields.Many2one(
        'account.account',
        string='Cuenta',
        related='move_line_id.account_id',
    )
    amount_total_signed = fields.Monetary(
        string='Total',
        store=True,
    )
    move_line_id = fields.Many2one(
        'account.move.line',
        string='Factura',
    )
    #Campo para filtrar las cuentas
    account_type = fields.Selection([
        ('asset_receivable', 'Cuentas por cobrar'),
        ('liability_payable', 'Cuentas por pagar')],
        string='Tipo de cuenta', compute='_compute_account_type', store=True
    )
        
    @api.depends('move_invoice_type')
    def _compute_account_type(self):
        for record in self:
            if record.move_invoice_type == 'out_invoice':
                record.account_type = 'asset_receivable'
            elif record.move_invoice_type == 'in_invoice':
                record.account_type = 'liability_payable'

    @api.onchange('move_line_id')
    def _onchange_move_line_id(self):
        if self.move_line_id:
            precision = self.currency_id.decimal_places
            amount_total_signed = abs(self.move_line_id.amount_currency)
            self.amount_total_signed = round(amount_total_signed, precision)
            self.document_type_id = self.move_line_id.move_id.l10n_latam_document_type_id
            
    @api.depends('invoice_name')
    def _compute_name(self):
        for record in self:
            if record.invoice_name:
                record.name = record.invoice_name
            else:
                record.name = 'Factura#' + str(record.id)
    
    def action_view_invoice(self):
        return {
            'name': 'Factura',
            'view_mode': 'form',
            'res_id': self.move_id.id,
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
