
from odoo import fields, models, api
from datetime import datetime
import logging
from collections import defaultdict


_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    seller_account = fields.Many2one(
        comodel_name='res.users',
        string="Vendedor",
        compute='_compute_seller',
        readonly=False,
        store=True
    )
    account_relational_name = fields.Char(
        string="Nombre de cuenta relacionada"
    ) 

    amount_no_sign_pen = fields.Monetary(
        string='Amount (Positive)',
        compute='_compute_amount_no_sign',
        store=True,
        currency_field='currency_pen_id'
    )

    amount_no_sign_usd = fields.Monetary(
        string='Amount (Positive)',
        compute='_compute_amount_no_sign',
        store=True,
        currency_field='currency_usd_id'
    )
    letters_paid = fields.Boolean(
        string="Letras pagadas?",
        compute='_compute_letter_paid',
        store=True,
    )
    count_letter = fields.Boolean(
        string="Tiene Letras?",
        compute='_compute_count_letter',
        store=True,
    )
    report_account_letter_paid = fields.Boolean(
        string="Reporte Cuenta Pagada",
        compute='_compute_report_account_letter_paid',
        store=True,
    )
    account_payment_date = fields.Date(
        string="Fecha de Pago",
    )
    grouped_payments = fields.Boolean(
        string="Pagos Agrupados?",
        default=False
    )
    related_move_id = fields.Many2one(
        'account.move', 
        string='Factura Relacionada', 
        compute='_compute_related_move_id', 
        store=False)

    account_letter_id = fields.Many2one(
        'account.letter', 
        string='Canje de Letra Relacionado', 
        compute='_compute_account_letter_id', 
        store=True)

    @api.depends('move_id.letter_id')
    def _compute_account_letter_id(self):
        for move_line in self:
            move_line.account_letter_id = False
            if move_line.journal_id.name == "Letras por cobrar":
                move_line.account_letter_id = move_line.move_id.letter_id.id

    @api.depends('new_move_name')
    def _compute_related_move_id(self):
        for move_line in self:
            move_line.related_move_id = False
            if move_line.new_move_name: 
                related_move = self.env['account.move'].search([('name', '=', move_line.new_move_name),], limit=1)
                move_line.related_move_id = related_move.id

    @api.depends('move_name', 'journal_id', 'name', 'count_letter', 'account_relational_name')
    def _compute_new_move_name(self):
        for move_line in self:
            if move_line.journal_id.name == "Letras por cobrar":
                move_line.new_move_name = move_line.name
            elif move_line.grouped_payments and move_line.account_relational_name:
                move_line.new_move_name = move_line.account_relational_name
            else: 
                move_line.new_move_name = move_line.move_name

    @api.depends('journal_id.name', 'move_id.letter_line_id.letter_user_id', 'move_id.invoice_user_id')
    def _compute_seller(self):
        for record in self:
            if record.journal_id.name == 'Letras por cobrar' and record.move_id.letter_id:
                record.seller_account = record.move_id.letter_id.letter_line_ids[0].letter_user_id
            elif record.move_id:
                record.seller_account = record.move_id.invoice_user_id
            else:
                record.seller_account = False 

    @api.depends('amount_currency')
    def _compute_amount_no_sign(self):
        for record in self:
            if record.currency_id.name == 'PEN':
                record.amount_no_sign_pen = abs(record.amount_currency)
            if record.currency_id.name == 'USD':
                record.amount_no_sign_usd = abs(record.amount_currency)

    @api.depends('new_move_name', 'move_id', 'move_id.letter_id', 'move_id.letter_id.letter_line_ids')
    def _compute_count_letter(self):
        for record in self:
            if record.move_id.letter_id and record.move_id.letter_id.letter_line_ids:
                if record.new_move_name in record.move_id.letter_id.invoice_line_ids.mapped('name') or record.new_move_name in record.move_id.letter_id.invoice_line_ids.mapped('move_line_name'):
                    record.count_letter = True

    @api.depends('move_id', 'move_id.letter_id', 'move_id.letter_id.letter_line_ids', 'move_id.letter_id.letter_line_ids.payment_state', 'move_id.letter_id.number_letter', 'reconciled')
    def _compute_letter_paid(self):
        for record in self:
            if record.move_id.letter_id and record.move_id.letter_id.letter_line_ids:
                count_letter = record.move_id.letter_id.number_letter
                count_letter_paid = 0
                for letter in record.move_id.letter_id.letter_line_ids:
                    if letter.payment_state == 'paid':
                        count_letter_paid += 1

                if count_letter == count_letter_paid:
                    record.letters_paid = True

    @api.depends('l10n_pe_is_withholding_line', 'reconciled', 'account_id.deprecated', 'account_id.account_type', 'payment_date', 'new_date', 'parent_state', 'count_letter', 'letters_paid', 'journal_id.name', 'move_id.payment_state', 'amount_currency', 'amount_residual', 'matched_credit_ids', 'new_move_name')
    def _compute_report_account_letter_paid(self):
        for record in self:
            rules_basic = False
            letters_paid = False

            if record.account_id.account_type == 'asset_receivable' and record.journal_id.name != 'Letras por cobrar' and record.payment_date is not False and record.new_date is not False and record.parent_state == 'posted':
                rules_basic = True

            # Facturas sin letras
            if rules_basic and not record.count_letter and record.reconciled and record.account_id.deprecated is False and record.move_id.payment_state != "reversed" and record.move_type != "in_invoice":
                credit_ids = record.matched_credit_ids
                if record.l10n_pe_is_withholding_line is False:
                    self.credits(credit_ids, record)

            # Letras pagadas
            if record.reconciled and record.payment_date is not False and record.new_date is not False and record.journal_id.name == 'Letras por cobrar' and not record.count_letter:
                record.report_account_letter_paid = True 
                if record.matched_credit_ids:
                    
                    search_letter_in_followup = self.env['account.followup.paid'].search([('document_number','=', record.new_move_name), ('account_letter_id', '=', record.account_letter_id.id)])

                    if not search_letter_in_followup:
                        invoice_vals = {
                            'date': record.new_date,
                            'document_number': record.new_move_name,
                            'partner_id': record.partner_id.id,
                            'account_payment_date': record.matched_credit_ids[0].credit_move_id.date,
                            'seller_account': record.seller_account.id,
                            'amount_no_sign_pen': record.amount_no_sign_pen,
                            'amount_no_sign_usd': record.amount_no_sign_usd,
                            'account_move_line_id': record.id,
                            'related_move_id': record.related_move_id.id,
                            'account_letter_id': record.account_letter_id.id,
                        }
                        self.env['account.followup.paid'].create(invoice_vals)
                    record.account_payment_date = record.matched_credit_ids[0].credit_move_id.date          

            # Facturas pagadas parcialmente sin NC (con o sin detracción)
            if rules_basic and not record.count_letter and record.move_id.payment_state == "partial":
                credit_ids = record.matched_credit_ids
                if record.l10n_pe_is_withholding_line is False:
                    self.credits(credit_ids, record)
                
            if record.move_type == 'out_refund':
                record.report_account_letter_paid = False


    def credits(self, credit_ids, record):
        credit_totals = defaultdict(list)
        for credit in credit_ids:
            if credit.credit_move_id.move_type != 'out_refund' and credit.credit_move_id.journal_id.name != "Diferencia de cambio":
                month = credit.credit_move_id.date.month
                year = credit.credit_move_id.date.year

                credit_totals[(year, month)].append(credit)

        # Procesamos los créditos agrupados para cada mes y año
        for (year, month), credits in credit_totals.items():
            # Ordenamos los créditos por fecha para obtener el último crédito del mes
            credits_sorted = sorted(credits, key=lambda c: c.credit_move_id.date)
            
            # Obtenemos el último crédito del mes
            last_credit = credits_sorted[-1]

            total_amount_pen = 0
            total_amount_usd = 0

            for credit in credits:
                if credit.credit_currency_id.name == "PEN":
                    total_amount_pen += credit.credit_amount_currency

                elif credit.credit_currency_id.name == "USD":
                    total_amount_usd += credit.credit_amount_currency

            if total_amount_pen > 0 or total_amount_usd > 0:

                # Guardamos los cambios en la base de datos
                search_move_in_followup = self.env['account.followup.paid'].search([('account_move_line_id','=',record.id), ('year', '=', year), ('month', '=', month)])

                if search_move_in_followup:
                    search_move_in_followup.write({
                        'amount_no_sign_pen': total_amount_pen,
                        'amount_no_sign_usd': total_amount_usd,
                        'account_payment_date': last_credit.credit_move_id.date
                    })
                
                else:

                    invoice_vals = {
                        'date': record.new_date,
                        'document_number': record.new_move_name,
                        'partner_id': record.partner_id.id,
                        'account_payment_date': last_credit.credit_move_id.date,
                        'seller_account': record.seller_account.id,
                        'amount_no_sign_pen': total_amount_pen,
                        'amount_no_sign_usd': total_amount_usd,
                        'account_move_line_id': record.id,
                        'related_move_id': record.related_move_id.id,
                        'year': year,
                        'month': month,
                    }
                    self.env['account.followup.paid'].create(invoice_vals)
