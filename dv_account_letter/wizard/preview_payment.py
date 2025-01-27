from odoo import models, fields, api
from datetime import date
from odoo.exceptions import ValidationError

class PreviewPayment(models.TransientModel):
    _name = 'preview.payment'

    letter_line_id = fields.Many2one(
        'account.letter.line', 
        string='Línea de Letra', required=True)
    partner_id = fields.Many2one(
        'res.partner', 
        string='Socio', related='letter_line_id.partner_id')
    currency_id = fields.Many2one(
        'res.currency', 
        string='Moneda', related='letter_line_id.currency_id')
    amount = fields.Monetary(string='Monto', related='letter_line_id.amount_total')
    commission = fields.Monetary(string='Comisión', related='letter_line_id.commission')
    payment_type = fields.Selection(
        selection=[
            ('outbound', 'Enviar'),
            ('inbound', 'Recibir'),
        ],
        string='Tipo de Pago',
        compute='_compute_payment_type',
        required=True,
    )
    date = fields.Date(string='Fecha', required=True, default=fields.Date.today())
    ref = fields.Char(string='Memo')
    journal_id = fields.Many2one(
        'account.journal', 
        string='Diario', required=True,
        domain="[('type', 'in', ('bank', 'cash'))]")
    payment_method_line_id = fields.Many2one(
        'account.payment.method.line', 
        string='Método de Pago', required=True,
        domain="[('id', 'in', payment_method_line_ids)]"
    )
    payment_method_line_ids = fields.Many2many(
        'account.payment.method.line', 
        string='Métodos de Pago', compute='_compute_payment_method_ids')
    
    # def create(self, vals):
    #     #comprueba si está letter_line_id en vals
    #     if 'letter_line_id' in vals:
    #         self.amount = self.env['account.letter.line'].browse(vals['letter_line_id']).amount_total
    #         self.commission = self.env['account.letter.line'].browse(vals['letter_line_id']).commission
    #         self.currency_id = self.env['account.letter.line'].browse(vals['letter_line_id']).currency_id
    #     return super(PreviewPayment, self).create(vals)
    @api.depends('letter_line_id')
    def _compute_payment_type(self):
        for record in self:
            record.payment_type = 'inbound' if record.letter_line_id.move_invoice_type == 'out_invoice' else 'outbound'
    @api.depends('journal_id', 'payment_type')
    def _compute_payment_method_ids(self):
        for record in self:
            #Establecer los métodos de pago según el diario y el tipo de pago
            if record.journal_id and record.payment_type == 'inbound':
                record.payment_method_line_ids = record.journal_id.inbound_payment_method_line_ids
            elif record.journal_id and record.payment_type == 'outbound':
                record.payment_method_line_ids = record.journal_id.outbound_payment_method_line_ids
            else:
                record.payment_method_line_ids = False
    
    # Creación de pago
    def action_create_payment(self):
        if self.letter_line_id.move_invoice_type == 'in_invoice':
            partner_type = 'supplier'
        else:
            partner_type = 'customer'
        payment = self.env['account.payment'].create({
            'payment_type': self.payment_type,
            'partner_id': self.partner_id.id,
            'partner_type': partner_type,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'date': self.date,
            'journal_id': self.journal_id.id,
            'payment_method_line_id': self.payment_method_line_id.id,
            'ref': self.ref,
        })
        payment = payment.with_context(
			skip_account_move_synchronization=True)
        # Identificar la línea que tiene la cuenta "por cobrar" o "por pagar"
        receivable_payable_line = payment.line_ids.filtered(
            lambda l: l.account_id.account_type in ['asset_receivable', 'liability_payable']
        )
        if receivable_payable_line:
            receivable_payable_line.write({
                    'account_id': self.letter_line_id.account_id.id,
                })
        #Lineas de comisión
        if self.commission > 0:
            self.create_commission_lines(payment)
        payment.action_post()
        self.action_conciliate_payment(payment)
        self.letter_line_id.payment_id = payment.id
        self.letter_line_id.payment_state = 'paid'
        self.letter_line_id.letter_id.action_done()
    
    def create_commission_lines(self, payment):
        if not payment.line_ids:
            return
        #Preparación para el debito y credito
        precision = self.currency_id.decimal_places
        convertion_rate = round(self.get_convertion_rate(), 8)
        credit = 0.0
        debit = 0.0
        receivable_payable_line = payment.line_ids.filtered(
            lambda l: l.account_id.account_type in ['asset_receivable', 'liability_payable']
        )
        not_receivable_payable_line = payment.line_ids - receivable_payable_line
        if self.payment_type == 'inbound':
            commission = self.commission
            credit += round(receivable_payable_line.amount_currency * convertion_rate, precision) * -1
            debit += round(commission * convertion_rate , precision)
            debit += round((not_receivable_payable_line.amount_currency - commission) * convertion_rate, precision)
        else:
            commission = self.commission * -1
            debit += round(receivable_payable_line.amount_currency * convertion_rate, precision)
            credit += round((not_receivable_payable_line.amount_currency - commission) * convertion_rate, precision) * -1
            credit += round(commission * convertion_rate, precision) * -1
        account_move_lines = []
        # Primera línea por pagar o cobrar
        account_payable_lines = []
        account_payable_lines.append( {
            'name': receivable_payable_line.name,
            'account_id': receivable_payable_line.account_id.id,
            'partner_id': receivable_payable_line.partner_id.id,
            'amount_currency': receivable_payable_line.amount_currency,
            'currency_id': receivable_payable_line.currency_id.id,
            'date_maturity': receivable_payable_line.date_maturity,
        })

        account_move_lines.extend(account_payable_lines)
        # Segunda línea: cuenta no por cobrar o pagar
        account_not_payable_lines = []
        amount_currency = not_receivable_payable_line.amount_currency - commission
        account_not_payable_lines.append( {
            'name': not_receivable_payable_line.name,
            'account_id': not_receivable_payable_line.account_id.id,
            'partner_id': not_receivable_payable_line.partner_id.id,
            'amount_currency': amount_currency,
            'currency_id': not_receivable_payable_line.currency_id.id,
            'date_maturity': not_receivable_payable_line.date_maturity,
        })
        account_move_lines.extend(account_not_payable_lines)
        # Tercera línea: comisión
        commission_line = []
        commission_line.append( {
            'name': f'Comisión del pago de la letra {self.letter_line_id.name}',
            'account_id': self.env['account.letter.conf'].search([
                ('document_type', '=', 'commission'),
                ('currency_id', '=', self.currency_id.id)
            ], limit=1).account_id.id,
            'partner_id': self.partner_id.id,
            'amount_currency': commission,
            'currency_id': self.currency_id.id,
            'date_maturity': receivable_payable_line.date_maturity,
            'date': self.date,
        })
        account_move_lines.extend(commission_line)
        #Apunte contable de la diferencia
        debit = round(abs(debit), precision)
        credit = round(abs(credit), precision)
        if debit - credit != 0.0:
            difference_lines = []
            if debit > credit:
                account_type = 'income_other'
                amount_currency = round(credit - debit, precision)
            elif debit < credit:
                account_type = 'expense'
                amount_currency = round(credit - debit, precision)
            #Inversión de cuentas y montos para el caso proveedor
            # if self.letter_line_id.letter_id.type == 'in_invoice':
            #     account_type = 'income_other' if account_type == 'expense' else 'expense'
            #     amount_currency = amount_currency * -1
            account_id = self.env['account.letter.conf'].search([
                ('document_type', '=', 'difference'),
                ('account_type', '=', account_type),
            ], limit=1).account_id
            difference_lines.append({
                'name': 'Diferencia de cambio',
                'account_id': account_id.id,
                'partner_id': self.partner_id.id,
                'amount_currency': amount_currency,
                'currency_id': self.env.company.currency_id.id,
                'date': self.date,
                'date_maturity': self.date,
            })
            account_move_lines.extend(difference_lines)
        payment.move_id.line_ids.sudo().unlink()
        payment.move_id.write({'line_ids': [(0, 0, line) for line in account_move_lines]})

    #Metodo para obtener la tasa de cambio
    def get_convertion_rate(self):
        convertion_rate = self.env['res.currency']._get_conversion_rate(
            self.currency_id,
            self.env.company.currency_id,
            self.letter_line_id.company_id,
            self.date
        )
        return convertion_rate

    # Método para conciliar el pago con la letra del canje
    def action_conciliate_payment(self, payment):
        debit_lines = []
        credit_lines = []
        #debito letra
        for letter_line in self.letter_line_id.letter_id.move_id.line_ids.filtered(lambda x: x.name == self.letter_line_id.name):
            debit_lines.extend(letter_line)
        #credito pago
        for payment_line in payment.move_id.line_ids:
            credit_lines.extend(payment_line.filtered(lambda line: line.account_id.account_type in ['asset_receivable', 'liability_payable']))
        for debit_line, credit_line in zip(debit_lines, credit_lines):
            res = debit_line + credit_line
            (debit_line + credit_line).reconcile()
