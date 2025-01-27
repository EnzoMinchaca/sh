from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'retention.payment.wizard.ultimate'

    l10n_pe_withholding_subject_invoice_ids = fields.Many2many(
        'account.move', 'account_payment_register_withholding_subject_invoice_rel', 'account_payment_register_id', 'account_move_id',
        string='Facturas sujetas a retención', store=True
    )
    account_withholding_percent = fields.Float(
        string='Porcentaje de retención (%)', default=3, required=True
    )
    payment_difference_calculate = fields.Monetary(string='Diferencia de pago', currency_field='currency_id', 
        compute='_compute_l10n_pe_withholding_amount_difference', store=True
    )
    l10n_pe_withholding_document_number = fields.Char(
        string='Número de comprobante de retención')

    withholding_journal_id = fields.Many2one(
        comodel_name='account.journal',
        readonly=False)

    writeoff_account_id_set_by_user = fields.Boolean(default=False)

    state_button = fields.Boolean(help='Status del radio seleccionado', default=False)

    total_amount_static = fields.Float(store=True)

    l10n_pe_withholding_amount_currency = fields.Monetary(
        string='Monto de retención en moneda de la empresa', currency_field='company_currency_id', store=True)

    payment_difference_custom = fields.Monetary(currency_field='currency_id',
        compute='_compute_l10n_pe_withholding_amount', store=True
    )

    payment_date = fields.Date(string="Payment Date", required=True,
        default=fields.Date.context_today, store=True)

    status_new_date = fields.Boolean(default=False)

    retentions_for_invoice = {}
        
    def _compute_withholding_amount(self):
        sum_amount_retention = 0
        var_amount_retention = 0

        for invoice in self.l10n_pe_withholding_subject_invoice_ids:
            var_amount_retention = invoice.amount_retention

            if invoice.currency_id.name == 'PEN':
                var_amount_retention = round(var_amount_retention, 2)
            else:
                var_amount_retention *= self.get_exchange_rate_usd_to_pen(self.payment_date)
                var_amount_retention = round(var_amount_retention, 2)

            invoice.amount_retention_optional = var_amount_retention
            sum_amount_retention += var_amount_retention

        self.write({
            'total_amount_static': sum_amount_retention,
            'l10n_pe_withholding_amount_currency': sum_amount_retention,
            'payment_difference_custom': sum_amount_retention
        })

    # METODOS DE INICIO
    @api.model
    def create(self, vals):
        res = super(AccountPaymentRegister, self).create(vals)

        if 'writeoff_account_id_set_by_user' not in vals:
            vals['writeoff_account_id_set_by_user'] = False

        res._compute_withholding_amount()

        journal = self.env['account.journal'].search([
            ('l10n_pe_is_withhold_journal', '=', True)
        ], limit=1)
        if journal:
            res.withholding_journal_id = journal.id
        return res

    # METODOS ONCHANGE
    @api.onchange('l10n_pe_withholding_subject_invoice_ids')
    def _onchange_recompute_totals(self):
        self._validate_retention_option()
        self._compute_l10n_pe_withholding_amount()
        self._compute_amount_retention_optional()

    @api.onchange('payment_difference_handling')
    def _ochange_status_button(self):
        if self.payment_difference_handling == 'open':
            self.state_button = True
        else:
            self.state_button = False
    
    @api.onchange('writeoff_account_id')
    def _onchange_writeoff_account_id(self):
        self.writeoff_account_id_set_by_user = True

    @api.depends('l10n_pe_withholding_subject_invoice_ids')
    def _validate_retention_option(self):
        # Capturamos los valores iniciales de la factura
        invalid_invoices = self.l10n_pe_withholding_subject_invoice_ids.filtered(lambda inv: inv.amount_retention <= 0.0)

        if invalid_invoices:
            invoice_names = ", ".join(invalid_invoices.mapped('name'))
            message = f"Las siguientes facturas fueron eliminadas porque no queda nada por pagar: {invoice_names}."
            self._show_message(message)
            
        if invalid_invoices:
            self.write({'l10n_pe_withholding_subject_invoice_ids': [(3, invoice.id) for invoice in invalid_invoices]})

        for invoice in self.l10n_pe_withholding_subject_invoice_ids:
            var_amount_retention = 0
            if invoice.amount_retention_optional == 0:
                var_amount_retention = invoice.amount_retention

                if invoice.currency_id.name == 'PEN':
                    var_amount_retention = round(var_amount_retention, 2)
                else:
                    var_amount_retention *= self.get_exchange_rate_usd_to_pen(self.payment_date)
                    var_amount_retention = round(var_amount_retention, 2)

                invoice.amount_retention_optional = var_amount_retention  

    def _show_message(self,message):
        return{
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Notificación Retención',
                'type': 'warning',
                'message': message,
                'sticky': True,
            }
        }

    # METODOS DEPENDS
    @api.depends('l10n_pe_withholding_subject_invoice_ids.amount_retention_optional')
    def _compute_l10n_pe_withholding_amount(self):

        total_amount = 0
        for record in self:
                
            for invoice in record.l10n_pe_withholding_subject_invoice_ids:
                total_amount += invoice.amount_retention_optional
        
        if self.payment_difference_handling == 'reconcile':
            sum_amount_retention = self.total_amount_static

            sum_amount_retention_optional = 0
            for record in self:
                for invoice in record.l10n_pe_withholding_subject_invoice_ids:
                    sum_amount_retention_optional += invoice.amount_retention_optional

            if sum_amount_retention_optional > sum_amount_retention and self.payment_difference_calculate == 0:
                self.payment_difference_custom = total_amount

    @api.depends('payment_difference_custom','l10n_pe_withholding_amount_currency','writeoff_account_id_set_by_user')
    def _compute_l10n_pe_withholding_amount_difference(self):

        self._compute_l10n_pe_withholding_amount()
        
        self.payment_difference_calculate = round(self.payment_difference_custom - self.l10n_pe_withholding_amount_currency, 2)

        if self.writeoff_account_id_set_by_user == False:

            if self.payment_difference_calculate < 0:
                self.writeoff_account_id = self.env['account.account'].search([
                    ('code', '=', '7760000')
                ]).id
                self.writeoff_label = 'Diferencia de cambio'
            else:
                self.writeoff_account_id = self.env['account.account'].search([
                    ('code', '=', '6760000')
                ]).id
                self.writeoff_label = 'Diferencia de cambio'
        
        else:
            self.writeoff_account_id = self.writeoff_account_id

    # METODOS ESTANDAR
    @api.depends('l10n_pe_withholding_subject_invoice_ids.amount_retention_optional')
    def _compute_amount_retention_optional(self):
        total_amount_vol = 0

        total_amount_retention_optional = sum(invoice.amount_retention_optional for invoice in self.l10n_pe_withholding_subject_invoice_ids)

        total_amount_vol = self.l10n_pe_withholding_amount_currency - total_amount_retention_optional

        if self.l10n_pe_withholding_amount_currency > total_amount_retention_optional:
            self.l10n_pe_withholding_amount_currency -= (total_amount_vol)
        elif self.l10n_pe_withholding_amount_currency < total_amount_retention_optional: 
            self.l10n_pe_withholding_amount_currency += abs(total_amount_vol)
        else:
            pass

    def _prepare_withholding_lines(self):

        precision = self.currency_id.decimal_places
        withholding_lines = []
        # Longitud de las facturas
        total_moves = len(self.l10n_pe_withholding_subject_invoice_ids)
        
        decimal_verify = self.l10n_pe_withholding_amount_currency

        for move_id in self.l10n_pe_withholding_subject_invoice_ids:
            
            withholding_amount_currency = 0
            withholding_account_id = self.company_id.withholding_account_id
            if not withholding_account_id:
                raise UserError(
                    "Debe configurar una cuenta de retención desde Contabilidad > Configuración > Ajustes")

            if  self.payment_difference_handling == 'reconcile':
                withholding_amount_currency = move_id.amount_retention_optional
                diference_line = (self.payment_difference_calculate / total_moves) * -1
                price = round(withholding_amount_currency + diference_line, precision)
                decimal_verify -= price
            
            else:
                price = move_id.amount_retention_optional

            line_data = {
                'partner_id': self.partner_id.id,
                'currency_id': self.env.company.currency_id.id,
                'display_type': 'payment_term',
            }
            withholding_lines += [(0, 0, {
                **line_data,
                'name': f'Retención de {move_id.name}',
                'account_id': withholding_account_id.id,
                'price_unit': price,
                'quantity': 1,
                'tax_ids': False,
                'l10n_pe_withhold_invoice_id': move_id.id,
                'display_type': 'product',
            })]

        if decimal_verify != 0 and self.payment_difference_handling == 'reconcile':
            withholding_lines[-1][2]['price_unit'] += decimal_verify
        return withholding_lines

    def _create_withholding_move(self):
        self.ensure_one()
        withholding_invoice_names = self.l10n_pe_withholding_subject_invoice_ids.mapped(
            'name')
        
        move_type = ''
        if self.payment_type == 'inbound':
            move_type = 'in_invoice'
        elif self.payment_type == 'outbound':
            move_type = 'out_invoice'

        data = {
            'move_type': move_type,
            'ref': f"Retención de {withholding_invoice_names}",
            'journal_id': self.withholding_journal_id.id,
            'l10n_latam_document_type_id': self.env.ref('l10n_pe.document_type20').id,
            'l10n_latam_document_number': self.l10n_pe_withholding_document_number,
            'date': self.payment_date,
            'invoice_date': self.payment_date,
            'invoice_date_due': self.payment_date,
            'invoice_date': self.payment_date,
            'company_id': self.company_id.id,
            'partner_id': self.partner_id.id,
            'currency_id': self.env.company.currency_id.id,
            'line_ids': self._prepare_withholding_lines(),
        }
        withholding_account_move_id = self.env['account.move'].create(data)

        self._genarate_exchange_difference_lines(withholding_account_move_id)

        withholding_account_move_id._l10n_pe_configure_withholding_document_lines(self.l10n_pe_withholding_subject_invoice_ids, self.payment_difference_handling, self.payment_difference_calculate, self.l10n_pe_withholding_amount_currency)
        withholding_account_move_id.action_post()
        # Ajuste de los montos de retención
        self._reconcile_withholding(withholding_account_move_id)
        self._adjustment_of_withholding_amounts_()
        
    def write(self, vals):
        # Asegurarnos de que 'writeoff_account_id_set_by_user' no se modifique accidentalmente
        if 'writeoff_account_id' in vals and vals['writeoff_account_id'] != self.writeoff_account_id.id:
            self.writeoff_account_id_set_by_user = True  # Si se edita, lo marcamos como editado por el usuario

        return super(AccountPaymentRegister, self).write(vals)

    def _genarate_exchange_difference_lines(self,withholding_account_move_id):

        if self.payment_difference_calculate != 0 and self.payment_difference_handling != 'open':

            withholding_account_move_id.write({
                'line_ids': [(0, 0, {
                    'name': self.writeoff_label,
                    'account_id': self.writeoff_account_id.id,
                    'price_unit': abs(self.payment_difference_calculate),
                    'quantity': 1 if self.payment_difference_calculate > 0 else -1,
                    'tax_ids': False,
                    'display_type': 'product',
                })]
            })
        return

    def _reconcile_withholding(self, to_process):
        reconcile_domain = [('account_id.reconcile', '=', True),
                            ('account_id.account_type', 'in', ['asset_receivable', 'liability_payable'])]
        reconcile_domain_retention = [('l10n_pe_is_withholding_line', '=', True)]

        # Se iteran los apuntes contables de la factura creada
        for withhold_line_id in to_process.line_ids.filtered_domain(reconcile_domain):
            state = False

            # Se busca la factura de la linea de retención
            withholding_invoice_id = withhold_line_id.l10n_pe_withhold_invoice_id

            # Se busca el campo de la factura que tiene retención
            invoice_line_id = withholding_invoice_id.line_ids.filtered_domain(reconcile_domain_retention)
            #Factura sin retención
            if not invoice_line_id:
                for line in withholding_invoice_id.line_ids:
                    if abs(line.balance) > (withholding_invoice_id.amount_retention) and (line.account_id == withhold_line_id.account_id):
                        (withhold_line_id + line).reconcile()
                        state = True
                        break
                else:
                    raise UserError(f"Todos los apuntes contables han sido pagados para la factura {withholding_invoice_id.name}!")
            if state == True:
                continue
            (withhold_line_id + invoice_line_id).reconcile()

    def create_payments_with_retention(self):
        self.retentions_for_invoice.update({
            invoice.name: invoice.amount_retention_optional
            for invoice in self.l10n_pe_withholding_subject_invoice_ids
        })
        self._create_withholding_move()
        return

    def _adjustment_of_withholding_amounts_(self):

        facturas = self.env['account.move'].search([('name', 'in', list(self.retentions_for_invoice.keys()))])
        
        for factura in facturas:
            if factura.name in self.retentions_for_invoice:

                if factura.amount_retention_optional < self.retentions_for_invoice[factura.name]:
                    factura.amount_retention_optional = 0

                else:
                    amount_discount = 0
                    factura.status_retention_validate = True

                    if factura.currency_id.name == 'PEN':
                        amount_discount = self.retentions_for_invoice[factura.name]
                    else:
                        exchange_rate = self.get_exchange_rate_usd_to_pen(self.payment_date)
                        amount_discount = self.retentions_for_invoice[factura.name] / exchange_rate

                    factura.amount_retention -= amount_discount
                    factura.amount_retention = round(factura.amount_retention, 2)

        self.retentions_for_invoice.clear()
    
    def get_exchange_rate_usd_to_pen(self, payment_date):
        currency_usd = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        if not currency_usd:
            raise UserError('No se encontró la moneda USD.')

        currency_pen = self.env['res.currency'].search([('name', '=', 'PEN')], limit=1)
        if not currency_pen:
            raise UserError('No se encontró la moneda PEN.')
        
        exchange_rate = self.env['res.currency.rate'].search([
            ('currency_id', '=', currency_usd.id),
            ('name', '<=', payment_date)
        ], order='name desc', limit=1)
        if not exchange_rate:
            raise UserError('No se encontró un tipo de cambio para USD en la fecha de hoy.')

        return exchange_rate.inverse_company_rate