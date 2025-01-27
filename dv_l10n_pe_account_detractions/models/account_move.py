from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    # ==== l10n_pe_edi fields ====
    l10n_pe_detraction_date = fields.Date(
        string="Detraction Date",
        copy=False,
        help="Indicate the date of issuance of the detraction deposit certificate",
    )
    l10n_pe_detraction_number = fields.Char(
        string="Detraction", copy=False, help="Indicate the number of issuance of the detraction deposit certificate"
    )

    # ============================
    l10n_pe_spot_group_visible = fields.Boolean(
        string='Grupo de detracción visible', compute='_compute_l10n_pe_spot_group_visible', store=True)

    @api.depends('partner_id.country_id.code', 'company_id.partner_id.country_id.code', 'l10n_latam_document_type_id')
    def _compute_l10n_pe_spot_group_visible(self):
        """
        Grupo de detracción es visible si:
        - La empresa es de Perú
        - El socio es de Perú
        - El tipo de documento es 01 Factura
        """
        for record in self:
            pe_partner = record.partner_id.country_id.code == 'PE'
            pe_company = record.company_id.country_id.code == 'PE'
            is_invoice = record.l10n_latam_document_type_id.code == '01'
            not_entry_move = record.move_type != 'entry'
            if pe_partner and pe_company and is_invoice and not_entry_move:
                l10n_pe_spot_group_visible = True
            else:
                l10n_pe_spot_group_visible = False
            record.l10n_pe_spot_group_visible = l10n_pe_spot_group_visible

    l10n_pe_is_subject_to_spot = fields.Boolean(
        string='Sujeto a detracción', compute='_compute_l10n_pe_is_subject_to_spot', store=True, readonly=False)
    l10n_pe_spot_move_id = fields.Many2one(
        'account.move', string='Asiento de detracción', copy=False)
    l10n_pe_spot_code_id = fields.Many2one(
        'l10n_pe.spot.code', string='Codigo de detracción', compute='_compute_l10n_pe_is_subject_to_spot', store=True, readonly=False)
    l10n_pe_spot_code_percentage = fields.Float(
        string='Porcentaje de detracción', related='l10n_pe_spot_code_id.percentage', store=True)

    @api.depends('l10n_pe_spot_group_visible', 'invoice_line_ids.product_id.l10n_pe_withhold_code', 'invoice_line_ids.price_subtotal', 'invoice_date')
    def _compute_l10n_pe_is_subject_to_spot(self):
        """
        Una factura es sujeta a detracción si:
        - La empresa es de Perú
        - El socio es de Perú
        - Los productos son sujetos a detracción
        - El monto total en soles es mayor a 700
        - El tipo de docuento es 01 Factura

        - Si el porcentaje de detraccion es diferente a 0 y es mayor al porcentaje de retención
        """
        for record in self:
            l10n_pe_is_subject_to_spot = False
            l10n_pe_spot_code_id = False

            if record.l10n_pe_spot_group_visible and abs(record.amount_total_signed) > 700:
                max_percent = max(self.invoice_line_ids.mapped(
                    'product_id.l10n_pe_withhold_percentage'), default=0)
                product_spot_codes = self.invoice_line_ids.mapped(
                    'product_id.l10n_pe_withhold_code')
                l10n_pe_spot_code_id = self.env['l10n_pe.spot.code'].search(
                    [('percentage', '=', max_percent), ('code', 'in', product_spot_codes)], limit=1)
                if max_percent or l10n_pe_spot_code_id:
                    l10n_pe_is_subject_to_spot = True
                    l10n_pe_spot_code_id = l10n_pe_spot_code_id.id
            record.l10n_pe_is_subject_to_spot = l10n_pe_is_subject_to_spot
            record.l10n_pe_spot_code_id = l10n_pe_spot_code_id

    l10n_pe_spot_amount = fields.Monetary(
        string='Monto de detracción', currency_field='currency_id', compute='_compute_detraction_amount', store=True)
    l10n_pe_spot_amount_signed = fields.Monetary(
        string='Monto de detracción en moneda de la empresa con signo', currency_field='company_currency_id', compute='_compute_detraction_amount', store=True)
    l10n_pe_spot_amount_currency = fields.Monetary(
        string='Monto de detracción en moneda de la empresa', currency_field='company_currency_id', compute='_compute_detraction_amount', store=True)

    @api.depends('amount_total', 'l10n_pe_spot_code_percentage', 'amount_total_signed')
    def _compute_detraction_amount(self):
        for record in self:
            spot_percentage = record.l10n_pe_spot_code_percentage / 100
            l10n_pe_spot_amount = record.amount_total * spot_percentage # Este monto no se redondea
            l10n_pe_spot_amount_signed = round(
                record.amount_total_signed * spot_percentage)
            l10n_pe_spot_amount_currency = abs(l10n_pe_spot_amount_signed)
            record.write({
                'l10n_pe_spot_amount': l10n_pe_spot_amount,
                'l10n_pe_spot_amount_signed': l10n_pe_spot_amount_signed,
                'l10n_pe_spot_amount_currency': l10n_pe_spot_amount_currency,
            })

    def _post(self, soft=True):
        for move in self:
            if move.l10n_pe_is_subject_to_spot:
                move._l10n_pe_configure_spot_lines()
        res = super(AccountMove, self)._post(soft=soft)
        for move in self:
            if move.l10n_pe_is_subject_to_spot and move.company_id.l10n_pe_spot_mode == 'new_move':
                # Concilia el asiento de detracción con la factura
                if move.move_type == 'in_invoice':
                    partner_account_id = move.partner_id.property_account_payable_id
                else:
                    partner_account_id = move.partner_id.property_account_receivable_id
                spot_move = move.l10n_pe_spot_move_id
                spot_partner_line_id = spot_move.line_ids.filtered(
                    lambda r: r.account_id == partner_account_id)
                invoice_partner_line_id = move.line_ids.filtered(
                    lambda r: r.account_id == partner_account_id)
                reconcile_ids = spot_partner_line_id + invoice_partner_line_id
                reconcile_ids.reconcile()
        return res

    def _l10n_pe_configure_spot_lines(self):
        """
        Modifica la configuracion del account.payment.term temporalmente para que la primera linea de deuda tenga el monto de la detraccion
        y las siguientes lineas sumen el monto neto de la factura.
        Tipo de registro: off, same_move, new_move
        """
        l10n_pe_spot_mode = self.company_id.l10n_pe_spot_mode
        if l10n_pe_spot_mode == 'same_move':
            if self.invoice_payment_term_id:
                payment_term = self.invoice_payment_term_id
                # Valida que no haya lineas de tipo fixed
                if payment_term.line_ids.filtered_domain([('value', '=', 'fixed')]):
                    raise UserError(
                        "No se puede configurar la detracción porque el plazo de pago tiene lineas de tipo fijo.")
                # La primera linea es del plazo de pago es la detraccion
                new_payment_term_lines = [(5, 0, 0), (0, 0, {
                    'l10n_pe_is_spot_term_line': True,
                    'invoice_id': self.id,
                    'value': 'percent',
                    'value_amount': self.l10n_pe_spot_code_percentage,
                    'nb_days': 1,
                })]
                old_payment_term_lines = [(5, 0, 0)]
                # Reparte el monto neto en las siguientes lineas
                for line in payment_term.line_ids:
                    old_value = {
                        'nb_days': line.nb_days,
                        'value': 'percent',
                        'value_amount': line.value_amount,
                    }
                    new_value = {
                        'nb_days': line.nb_days + 1 if line.nb_days == 1 else line.nb_days,
                        'value': 'percent',
                        'value_amount': (line.value_amount * (1-self.l10n_pe_spot_code_percentage/100)/100),
                    }

                    old_payment_term_lines.append((0, 0, old_value))
                    new_payment_term_lines.append((0, 0, new_value))

                payment_term.write({'line_ids': new_payment_term_lines, 'display_on_invoice': False})
                self._compute_needed_terms()
                self._compute_tax_totals()
                self._compute_show_payment_term_details()
                payment_term.write({'line_ids': old_payment_term_lines, 'display_on_invoice': False})
            else:
                # Si no hay plazo de pago, utiliza el campo de fecha de vencimiento para crear uno temporal
                if not self.invoice_date_due or not self.invoice_date:
                    raise UserError(
                        "No se puede configurar la retención porque no hay fecha de vencimiento o fecha de factura.")
                days_to_pay = (self.invoice_date_due - self.invoice_date).days
                AccountPaymentTerm = self.env['account.payment.term']
                payment_term = AccountPaymentTerm.create({
                    'name': self.invoice_date_due.strftime('%d/%m/%Y'),
                    'note': f'Plazo de pago temporal para la detracción de la factura {self.name}',
                    'line_ids': [(0, 0, {
                        'l10n_pe_is_spot_term_line': True,
                        'invoice_id': self.id,
                        'value': 'fixed',
                        'value_amount': self.l10n_pe_spot_amount_currency,
                        'nb_days': 1,
                    }), (0, 0, {
                        'value': 'percent',
                        'value_amount': 100,
                        'nb_days': days_to_pay,
                    })]
                })
                self.invoice_payment_term_id = payment_term.id
                self._compute_needed_terms()
                self._compute_tax_totals()
                self._compute_show_payment_term_details()
                self.invoice_payment_term_id.active = False
                
        elif l10n_pe_spot_mode == 'new_move':
            l10n_pe_spot_receivable_account_id = self.company_id.l10n_pe_spot_receivable_account_id
            l10n_pe_spot_payable_account_id = self.company_id.l10n_pe_spot_payable_account_id
            l10n_pe_spot_journal_id = self.company_id.l10n_pe_spot_journal_id
            if not l10n_pe_spot_receivable_account_id or not l10n_pe_spot_payable_account_id or not l10n_pe_spot_journal_id:
                raise UserError(
                    "No se puede configurar la detracción porque no hay cuenta o diario de detracciones configurada.")
            # Crea un asiento contable con la cuenta por pagar (si es una factura de proveedor) o cobrar (si es una factura de cliente)
            if self.move_type == 'in_invoice':
                partner_account_id = self.partner_id.property_account_payable_id
                spot_account_id = l10n_pe_spot_payable_account_id
                spot_debit_amount = 0
                spot_credit_amount = self.l10n_pe_spot_amount_currency
                partner_debit_amount = self.l10n_pe_spot_amount_currency
                partner_credit_amount = 0
            else:
                partner_account_id = self.partner_id.property_account_receivable_id
                spot_account_id = l10n_pe_spot_receivable_account_id
                partner_debit_amount = 0
                partner_credit_amount = self.l10n_pe_spot_amount_currency
                spot_debit_amount = self.l10n_pe_spot_amount_currency
                spot_credit_amount = 0
                
            if not partner_account_id:
                raise UserError(
                    "No se puede configurar la detracción porque no hay cuenta de detracciones configurada.")
            move_vals = {
                'move_type': 'entry',
                'journal_id': l10n_pe_spot_journal_id.id,
                'company_id': self.company_id.id,
                'date': self.date,
                'partner_id': self.partner_id.id,
                'ref': f'Detracción de {self.name}',
                'line_ids': [(0, 0, {
                    'name': f'Detracción de {self.name}',
                    'partner_id': self.partner_id.id,
                    'account_id': partner_account_id.id,
                    'debit': partner_debit_amount,
                    'credit': partner_credit_amount,
                }), (0, 0, {
                    'name': f'Detracción de {self.name}',
                    'partner_id': self.partner_id.id,
                    'account_id': spot_account_id.id,
                    'debit': spot_debit_amount,
                    'credit': spot_credit_amount,
                })],
            }
            self.l10n_pe_spot_move_id = self.env['account.move'].create(move_vals)
            self.l10n_pe_spot_move_id.action_post()
            
    def button_draft(self):
        super(AccountMove, self).button_draft()
        for move in self:
            if move.company_id.l10n_pe_spot_mode == 'same_move':
                if move.l10n_pe_is_subject_to_spot and not self.invoice_payment_term_id.active:
                    move.invoice_payment_term_id = False
            elif move.company_id.l10n_pe_spot_mode == 'new_move':
                if move.l10n_pe_spot_move_id:
                    move.l10n_pe_spot_move_id.button_draft()
                    move.l10n_pe_spot_move_id.unlink()