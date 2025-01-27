from odoo import models, api, fields
from odoo.exceptions import UserError

class MassivePaymentRegister(models.TransientModel):
    _name= 'massive.payment.register'

    list_invoices_ids = fields.Many2many(
        'account.move', 'account_payment_register_massive', 'account_payment_register_id', 'account_move_id',
        string='Facturas a pagar', store=True
    )

    amount = fields.Monetary(string='Monto', compute='_compute_update_incoices_and_amount_total')

    amount_aux = fields.Monetary(string='Monto auxiliar', compute='_compute_calculate_amount_payment')

    payment_date = fields.Date(string="Payment Date", required=True,
        default=fields.Date.context_today, store=True)

    communication = fields.Char(string='Memo', store=True)

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        compute='_compute_currency_id', store=True, readonly=False, precompute=True,
        help="The payment's currency.")

    payment_difference = fields.Monetary(
        string='Diferencia de pago',
        compute='_compute_payment_difference',
        currency_field='currency_id')

    payment_difference_handling = fields.Selection(
        string="Manejo de diferencia de pagos",
        selection=[('open', 'Mantener abierto'), ('reconcile', 'Marcar como pagado en su totalidad')],
        default='open',
        store=True,
        readonly=False,)

    writeoff_account_id = fields.Many2one(
        comodel_name='account.account',
        string="Publicar diferencia en",
        copy=False)

    writeoff_label = fields.Char(string='Etiqueta', default='Diferencia de pago')

    payment_type = fields.Selection(
        selection=[
            ('outbound', 'Enviar'),
            ('inbound', 'Recibir'),
        ],
        string='Tipo de Pago', store=True)

    payment_method_line_id = fields.Many2one(
        'account.payment.method.line', 
        string='Método de Pago',
        domain="[('id', 'in', payment_method_line_ids)]",)

    payment_method_line_ids = fields.Many2many(
        'account.payment.method.line', 
        string='Métodos de Pago')

    journal_id = fields.Many2one(
        'account.journal', 
        string='Diario', store=True,
        domain="[('type', 'in', ('bank', 'cash'))]")

    state_group = fields.Boolean()

    group_payment = fields.Boolean(string='Agrupar pagos',
        default=False,
        store=True)

    @api.model
    def create(self, vals):
        res = super(MassivePaymentRegister, self).create(vals)
        journal = self.env['account.journal'].search([
            ('type', 'in', ('bank', 'cash')),
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        if journal:
            res.journal_id = journal.id

        invoice = res.list_invoices_ids[0]
        res.payment_type = 'inbound' if invoice.move_type == 'out_invoice' else 'outbound'
        res.payment_method_line_ids = res.journal_id.inbound_payment_method_line_ids if res.payment_type == 'inbound' else res.journal_id.outbound_payment_method_line_ids
        res.payment_method_line_id =res.env['account.payment.method.line'].search([
            ('id', 'in', res.payment_method_line_ids.ids),
            ('company_id', '=', res.env.company.id)
        ], limit=1) or False

        res.state_group = True if len(res.list_invoices_ids) > 1 else False

        return res

    # ONCHANGE METHODS
    @api.onchange('list_invoices_ids')
    def _onchange_trigger_method(self):
        self._compute_calculate_amount_payment()
    
    # DEPENDS METHODS
    @api.depends('list_invoices_ids.amount_to_payment')
    def _compute_calculate_amount_payment(self):
        sum_amount = 0
        for invoice in self.list_invoices_ids:
            sum_amount += invoice.amount_to_payment
        self.amount_aux = sum_amount

        if self.amount_aux != self.amount:
            self.amount = self.amount_aux

        if len(self.list_invoices_ids) > 1:
            self.state_group = True
        else:
            self.state_group = False

        memo_list = [invoice.name for invoice in self.list_invoices_ids]
        self.communication = ' '.join(memo_list)

    @api.depends('amount')
    def _compute_payment_difference(self):
        amount = self.amount
        if amount != self.amount_aux:
            self.payment_difference = self.amount_aux - amount
            self.amount = amount
        else:
            self.payment_difference = 0.0

    @api.depends('journal_id')
    def _compute_currency_id(self):
        self.currency_id = self.env.user.company_id.currency_id or self.journal_id.currency_id

    @api.depends('payment_date','currency_id')
    def _compute_update_incoices_and_amount_total(self):
        memo_list = [invoice.name for invoice in self.list_invoices_ids]
        self.communication = ' '.join(memo_list)

        self.amount = self.calculate_total_in_currency(
            self.currency_id.name,
            self.list_invoices_ids,
            self.payment_date)

    # BUSINESS METHODS
    def calculate_total_in_currency(self, currency_code, invoices, date_wizardd):
        target_currency = self.env['res.currency'].search([('name', '=', currency_code)], limit=1)
        if not target_currency:
            raise UserError(f"La moneda '{currency_code}' no existe en el sistema.")

        total = 0.0
        date = date_wizardd

        for invoice in invoices:
            invoice_currency = invoice.currency_id

            converted_amount = invoice_currency._convert(
                invoice.amount_total,
                target_currency,
                invoice.company_id,
                date
            )
            invoice.currency_id_to_payment = target_currency
            invoice.amount_to_payment = converted_amount
            total += converted_amount

        return total

    def execute_register_payment(self):

        precision = self.currency_id.decimal_places

        total_amount = 0
        partner = None
        invoice_lines = []

        for invoice in self.list_invoices_ids:
            if invoice.amount_to_payment <= 0:
                raise ValueError("El monto a pagar debe ser mayor a cero")
            if partner and partner != invoice.partner_id:
                raise ValueError("Las facturas deben pertenecer al mismo cliente.")

            total_amount += invoice.amount_to_payment
            invoice_lines.append((invoice, invoice.amount_to_payment))

        partner = self.list_invoices_ids[0].partner_id

        # Crear el pago
        payment = self.env['account.payment'].create({
            'ref': self.communication,
            'partner_id': partner.id,
            'amount': total_amount,
            'currency_id': self.currency_id.id,
            'date': self.payment_date,
            'payment_method_line_id': self.payment_method_line_id.id,
            'journal_id': self.journal_id.id,
            'payment_type': self.payment_type,
            'partner_type': 'customer',
        })

        payment = payment.with_context(skip_account_move_synchronization=True)

        reconcile_domain = [('account_id.account_type', 'in', ['asset_receivable', 'liability_payable'])]

        # Extraer la cuenta por pagar del movimiento de pago
        origin_payment_line = payment.move_id.line_ids.filtered_domain(reconcile_domain)
        # Generar los apuntes contables correspondientes
        account_move_lines = []

        # Crear los apuntes contables por factura
        for invoice in self.list_invoices_ids:
            invoice_amount = invoice.amount_to_payment

            account_move_lines.append({
                'account_id': origin_payment_line.account_id.id,
                'partner_id': invoice.partner_id.id,
                'name': invoice.name,
                'amount_currency': - round(invoice_amount, precision), # Va a credito
                'currency_id': self.currency_id.id,
                'date_maturity': origin_payment_line.date_maturity,
            })
        
        # Crear el apunte contable del monto total
        account_move_lines.append({
            'account_id': origin_payment_line.account_id.id,
            'partner_id': partner.id,
            'name': origin_payment_line.name,
            'amount_currency': round(total_amount, precision), # Va a debito
            'currency_id': self.currency_id.id,
            'tax_ids': [(6, 0, origin_payment_line.tax_ids.ids)],
            'date_maturity': origin_payment_line.date_maturity,
        })

        payment.move_id.line_ids.sudo().unlink()
        payment.move_id.write({'line_ids': [(0, 0, line) for line in account_move_lines]})
        payment.move_id.action_post()

        # ====================================================================================
        for invoice, amount in invoice_lines:
            
            reconcile_domain = [('account_id.reconcile', '=', True),
                            ('account_id.account_type', 'in', ['asset_receivable', 'liability_payable']),
                            ('name','=',invoice.name)]

            lines_to_reconcile = payment.move_id.line_ids.filtered_domain(reconcile_domain)
            
            # Filtramos los apuntes contables con la misma cuenta de la factura y con un balance mayor al monto a pagar
            invoice_line_to_reconcile = invoice.line_ids.filtered(lambda l: l.account_id == lines_to_reconcile.account_id)

            for line in invoice_line_to_reconcile:
                if amount <= 0:
                    break
                if line.amount_residual >= amount:
                    (lines_to_reconcile + line).reconcile()
                    amount = 0
                # Esto no debería de pasar
                else:
                    amount -= line.amount_residual
                    (lines_to_reconcile + line).reconcile()

        # ====================================================================================
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'res_id': payment.id,
            'view_mode': 'form',
            'target': 'current',
        }