# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import timedelta, date
from odoo.exceptions import UserError
from lxml import etree
from decimal import Decimal, ROUND_HALF_UP

class AccountLetter(models.Model):
    _name = 'account.letter'
    _description = 'Canje de letras'

    name = fields.Char(
        string=u'Nro. Canje', 
        index=True, default=lambda self: ('Borrador'), readonly=True,
        copy=False,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Borrador'),
            ('checked', 'Comprobado'),
            ('redeemed', 'En Cartera'),
            ('billing', 'En Cobranza'),
            ('done', 'Cerrado'),
            ('cancel', 'Cancelado'),
        ],
        string='Estado',
        default='draft',
        required=True, readonly=True,
    )
    type = fields.Selection([
        ('out_invoice', 'Cliente'), 
        ('in_invoice', 'Proveedor')], 
        string='Tipo'
    )
    redeemed_type = fields.Selection(
        selection=[
            ('origin', 'Origen'),
            ('renewal', 'Renovación'),
            ('protested', 'Refinanciamiento'),
        ],
        string='Tipo de Canje',
        compute='_compute_redeemed_type',
        readonly=True,
    )
    partner_id = fields.Many2one(
        'res.partner', 
        string='Socio',
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Diario',
        domain="[('name', 'ilike', 'letra')]",
    )
    invoice_date = fields.Date(
        string='Fecha Canje',
        default=fields.Date.context_today,
    )
    payment_reference = fields.Char(
        string='Referencia',
        index='trigram',
        copy=False,
    )
    invoice_line_ids = fields.One2many(
        'account.charge.invoices',
        'letter_id',
        string='Facturas',
    )
    letter_line_ids = fields.One2many(
        'account.letter.line',
        'letter_id',
        string='Letras',
        copy=False,
    )
    account_move_line_ids = fields.Many2many(
        'account.move.line',
        string='Apunte Contable',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    move_id = fields.Many2one(
        'account.move', 
        string='Asiento Contable',
        copy=False, 
        readonly=True)

    # ------------------------------------------------------------
    # Campos para calcular las letras
    # ------------------------------------------------------------
    number_letter = fields.Integer(
        string='Cantidad de Letras',
        default=1,
    )
    letter_end_date = fields.Date(
        string='Fecha de Venc. 1ra Letra',
    )
    range_date = fields.Integer(
        string='Rango de dias',
        default=1,
    )
    type_payment = fields.Selection(
        selection=[
            ('partial', 'Parcial'),
            ('total', 'Total'),
        ],
        string='Pago', default='total',
    )
    partial_amount = fields.Monetary(
        string='Importe Parcial',
        currency_field='currency_id',
        digits=(10, 2),
    )
    rest_amount = fields.Monetary(
        string='Monto Restante',
        currency_field='currency_id',
        compute='_compute_rest_amount',
        digits=(10, 2),
    )
    retention_percent = fields.Integer(
        string='%. de Retención',
        default=0,
    )
    retention_amount = fields.Monetary(
        string='Importe de retención',
        currency_field='currency_id',
        compute='_compute_retention_amount',
    )
    total_amount_with_retention = fields.Monetary(
        string='Total con retención',
        currency_field='currency_id',
        compute='_compute_retention_amount',
    )

    @api.depends('invoice_line_ids', 'letter_line_ids')
    def _compute_rest_amount(self):
        if not self.invoice_line_ids:
            self.rest_amount = 0.0
            return
        for record in self:
            precision = record.currency_id.decimal_places
            invoice_amount_total = sum(line.amount_total_signed for line in record.invoice_line_ids)
            letter_amount_total = sum(line.amount_total for line in record.letter_line_ids)
            diference = (invoice_amount_total) - (letter_amount_total)
            if self.letter_line_ids:
                diference -= round(invoice_amount_total * record.retention_percent / 100, precision)
            record.rest_amount = diference
    
    @api.depends('invoice_line_ids','retention_percent')
    def _compute_retention_amount(self):
        for record in self:
            if not record.invoice_line_ids:
                record.retention_amount = 0.0
                record.total_amount_with_retention = 0.0
                return
            precision = record.currency_id.decimal_places
            invoice_amount_total = sum(line.amount_total_signed for line in record.invoice_line_ids)
            record.retention_amount = round(invoice_amount_total * record.retention_percent / 100, precision)
            record.total_amount_with_retention = invoice_amount_total - record.retention_amount

    def create_letters(self):
        if not self.number_letter:
            raise UserError('Necesitas añadir la cantidad de letras.')
        if not self.letter_end_date:
            raise UserError('Necesitas añadir la fecha de vencimiento.')
        if not self.range_date:
            raise UserError('Necesitas añadir el rango de dias.')
        if self.number_letter > 0:
            letter_amount_total = self.calculate_letter_amount_total()
            if letter_amount_total > 0:
                 #Calculo de la fecha de vencimiento de la primera letra
                if self.letter_line_ids and self.range_date:
                    expiration_date = self.letter_line_ids[-1].expiration_date + timedelta(days=self.range_date)
                elif self.letter_end_date and self.range_date:
                    expiration_date = self.letter_end_date
                for i in range(self.number_letter):
                    self.letter_line_ids = [(0, 0, {
                        'expiration_date': expiration_date,
                        'amount_total': letter_amount_total,
                        'letter_id': self.id,
                        'sequence': i + 1,
                    })]
                    expiration_date += timedelta(days=self.range_date)
    
    #Metodo para calcular el importe de la letra
    def calculate_letter_amount_total(self):
        letter_amount_total = 0.0
        if self.type_payment == 'total':
            rest_amount = self.rest_amount - self.retention_amount
            letter_amount_total = rest_amount / self.number_letter
        elif self.type_payment == 'partial':
            if self.partial_amount > 0 and self.partial_amount <= self.rest_amount:
                partial_amount = self.partial_amount - (self.partial_amount * self.retention_percent / 100)
                letter_amount_total = partial_amount / self.number_letter
        return letter_amount_total

    # ------------------------------------------------------------
    # Acciones de Estados de letras
    # ------------------------------------------------------------       
    
    #Estado de Borrador
    def action_draft(self):
        self.state = 'draft'
    
    #Estado de Comprobado
    def action_checked(self):
        if not self.invoice_line_ids:
            raise UserError('Necesitas añadir comprobantes antes de validar.')
        if not self.invoice_date:
            raise UserError('Necesitas añadir la fecha de canje.')
        if not self.journal_id:
            raise UserError('Necesitas añadir el diario.')
        if self.redeemed_type == 'protested':
            #Verificación de letras protestadas y pagadas
            letters_name = []
            for letter in self.invoice_line_ids:
                letters_name.append(letter.move_line_id.name)
            for letter in self.protested_parent_id.letter_line_ids:
                if letter.name in letters_name and letter.payment_state == 'paid':
                    raise UserError('La letra %s ya ha sido pagada.' % letter.name)
        self.state = 'checked'

    #Estado de En Cartera
    def action_redeemed(self):
        if not self.letter_line_ids:
            raise UserError('Necesitas añadir letras antes de canjear.')
        if any(not letter.nro_letter for letter in self.letter_line_ids):
            raise UserError('Necesitas añadir el número de letra antes de canjear.')
        if self.rest_amount != 0:
            raise UserError('El importe restante debe ser 0 para canjear.')
        #Verificación de letras protestadas y pagadas
        if self.redeemed_type == 'protested':
            letters_name = []
            for letter in self.invoice_line_ids:
                letters_name.append(letter.move_line_id.name)
            for letter in self.protested_parent_id.letter_line_ids:
                if letter.name in letters_name and letter.payment_state == 'paid':
                    raise UserError('La letra %s ya ha sido pagada.' % letter.name)
        #Tipo de cambio
        precision = self.currency_id.decimal_places
        convertion_rate = round(self.get_convertion_rate(), 8)
        decimal_str = '1.' + '0' * precision
        credit = float(0.00)
        debit = float(0.00)
        #Apunte contable del comprobante
        account_move_lines = []
        for invoice_line in self.invoice_line_ids.sudo():
            if invoice_line.move_invoice_type == 'out_invoice':
                amount_total = (invoice_line.amount_total_signed - round(invoice_line.amount_total_signed * self.retention_percent/100,precision)) * -1
                credit_operation = amount_total * convertion_rate
                str_credit_calcule = str(credit_operation)
                round_credit_calcule = Decimal(str_credit_calcule).quantize(Decimal(decimal_str), rounding=ROUND_HALF_UP)
                pre_credit_calcule = float(round_credit_calcule)
                credit += pre_credit_calcule
            else:
                amount_total = (invoice_line.amount_total_signed - round(invoice_line.amount_total_signed * self.retention_percent/100,precision))
                debit_operation = amount_total * convertion_rate
                str_debit_calcule = str(debit_operation)
                round_debit_calcule = Decimal(str_debit_calcule).quantize(Decimal(decimal_str), rounding=ROUND_HALF_UP)
                pre_debit_calcule = float(round_debit_calcule)
                debit += pre_debit_calcule
            account_move_lines.append({
                'name': invoice_line.move_line_name,
                'account_id': invoice_line.account_id.id,
                'partner_id': invoice_line.partner_id.id,
                'amount_currency': amount_total,
                'currency_id': invoice_line.currency_id.id,
                'date': fields.Date.today(),
                'date_maturity': invoice_line.move_id.invoice_date_due,
            })
            invoice_line.move_id.sudo().write({
                'redeemed_state': 'redeemed',
                'letter_id': self.id,
            })
        #Apunte contable de las letras
        account_letter_lines = []
        for letter_line in self.letter_line_ids:
            if letter_line.move_invoice_type == 'out_invoice':
                amount_total = letter_line.amount_total
                debit_operation = amount_total * convertion_rate
                str_debit_calcule = str(debit_operation)
                round_debit_calcule = Decimal(str_debit_calcule).quantize(Decimal(decimal_str), rounding=ROUND_HALF_UP)
                pre_debit_calcule = float(round_debit_calcule)
                debit += pre_debit_calcule
            else:
                amount_total = letter_line.amount_total * -1
                credit_operation = amount_total * convertion_rate
                str_credit_calcule = str(credit_operation)
                round_credit_calcule = Decimal(str_credit_calcule).quantize(Decimal(decimal_str), rounding=ROUND_HALF_UP)
                pre_credit_calcule = float(round_credit_calcule)
                credit += pre_credit_calcule
            account_letter_lines.append({
                'name': letter_line.nro_letter,
                'account_id': letter_line.account_id.id,
                'partner_id': letter_line.partner_id.id,
                'amount_currency': amount_total,
                'currency_id': letter_line.currency_id.id,
                'date': fields.Date.today(),
                'date_maturity': letter_line.expiration_date,
            })
        account_move_lines.extend(account_letter_lines)
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
            # if self.type == 'in_invoice':
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
                'date': fields.Date.today(),
                'date_maturity': fields.Date.today(),
            })
            account_move_lines.extend(difference_lines)
        account_move = self.env['account.move'].sudo().create({
            'ref': self.name,
            'date': self.invoice_date,
            'journal_id': self.journal_id.id,
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'letter_id': self.id,
            'line_ids': [(0, 0, line) for line in account_move_lines],
        })
        account_move.action_post()
        self.move_id = account_move.id
        self.state = 'redeemed'
        self.account_move_line(account_move)
        #if not (self.renewal_parent_id or self.protested_parent_id):
        self.action_reconcile_related_invoices(account_move)
    
    #Metodo para obtener la tasa de cambio
    def get_convertion_rate(self):
        convertion_rate = self.env['res.currency']._get_conversion_rate(
            self.currency_id,
            self.env.company.currency_id,
            self.company_id,
            self.invoice_date
        )
        return convertion_rate
    
    #Metodo para el apunte contable
    def account_move_line(self, account_move_line_ids):
        if account_move_line_ids:
            move_line_ids = []
            for record in account_move_line_ids.line_ids:
                move_line_ids.append(record.id)
            self.account_move_line_ids = [(6, 0, move_line_ids)]
    
    #Metodo para conciliar las facturas relacionadas
    def action_reconcile_related_invoices(self, move_id):
        debit_lines = []
        credit_lines = []
        #Línea por cobrar o por pagar de las facturas, notas de crédito o letras
        for invoice_line in self.invoice_line_ids:   
            credit_lines.extend(invoice_line.move_id.line_ids.filtered(lambda line: line.account_id.id == invoice_line.account_id.id and line.name in [rec.name for rec in move_id.line_ids]))
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

    #Estado Cerrado
    def action_done(self):
        pending_letters_count = sum(1 for letter in self.letter_line_ids if letter.payment_state == 'pending')
        if pending_letters_count > 1:
            return
        # Verificar que todas las letras de los canjes renovados ('renewal_ids') relacionados estén pagadas
        all_renewals_paid = self.renewal_ids and all(letter.payment_state == 'paid' for renewal in self.renewal_ids for letter in renewal.letter_line_ids)
        # Verificar que todas las letras de los canjes refinanciados ('protested_ids') relacionados estén pagadas
        all_protested_paid = self.protested_ids and all(letter.payment_state == 'paid' for protested in self.protested_ids for letter in protested.letter_line_ids)
        if self.renewal_ids and self.protested_ids:
            condition = all_renewals_paid and all_protested_paid
        else:
            condition = all_renewals_paid or all_protested_paid
        #Verificar que todas las letras esten en estado pagado
        if all(letter.payment_state == 'paid' for letter in self.letter_line_ids):
            self.state = 'done'
        elif condition:
            self.state = 'done'

        if self.renewal_parent_id or self.protested_parent_id:
            related_letters = self.renewal_parent_id and self.protested_parent_id
            for rec in related_letters:
                rec.action_done()
    
    #Estado Cancelado
    def action_cancel(self):
        if self.renewal_parent_id or self.protested_parent_id:
            related_letters = self.renewal_parent_id or self.protested_parent_id
            #Buscar el nombre de las letras del canje relacionado
            letters_name = []
            for letter in related_letters.letter_line_ids:
                letters_name.append(letter.name)
            #Busca el número de letra en charge_invoices
            for invoice_line in self.invoice_line_ids:
                if invoice_line.move_line_id.name in letters_name:
                    for letter in related_letters.letter_line_ids.filtered(lambda l: l.name == invoice_line.move_line_id.name):
                        if letter.payment_state != 'protested':
                            letter.payment_state = 'pending'
        if self.move_id:
            self.move_id.button_draft()
            self.move_id.unlink()
        self.state = 'cancel'

        if self.letter_line_ids:
            for letter in self.letter_line_ids:
                letter.payment_state = 'cancelled'

        if self.invoice_line_ids:
            for invoice in self.invoice_line_ids:
                invoice.move_id.write({
                    'redeemed_state': 'not_redeemed',
                    'letter_id': False,
                })
    #Metodo para el cálculo del nombre de la letra
    @api.model
    def create(self, vals):
        if 'type' in vals:
            if vals['type'] == 'out_invoice':
                prefix = 'CLC'
            else:
                prefix = 'CLP'
            sequence = self.env['ir.sequence'].next_by_code('account.letter')
            vals['name'] = f'{prefix}{sequence}' if sequence else f"{prefix}{vals.get('id', '')}"
        return super(AccountLetter, self).create(vals)

    # ------------------------------------------------------------
    # Pagos de las letras
    # ------------------------------------------------------------
    payment_ids = fields.Many2many(
        'account.payment',
        string='Pagos',
        compute='compute_payment_ids',
        store=True
    )
    count_payment = fields.Integer(
        string='Cantidad de Pagos',
        compute='compute_payment_ids',
        store=True
    )
    @api.depends('letter_line_ids.payment_id')
    def compute_payment_ids(self):
        for record in self:
            record.payment_ids = record.letter_line_ids.mapped('payment_id')
            record.count_payment = len(record.payment_ids)
    #Metodo para el botón de abrir pagos relacionados
    def action_open_related_payments(self):
        self.ensure_one()
        payments = self.mapped('payment_ids')
        if self.type == 'out_invoice':
            action = self.env["ir.actions.actions"]._for_xml_id("account.action_account_payments")
        else:
            action = self.env["ir.actions.actions"]._for_xml_id("account.action_account_payments_payable")
        if len(payments) > 0:
            action['domain'] = [('id', 'in', payments.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
    # ------------------------------------------------------------
    # Renovación de las letras
    # ------------------------------------------------------------
    is_renewal = fields.Boolean(
        string='Renovación',
        compute='compute_renewal_protested',
    )
    renewal_ids = fields.Many2many(
        'account.letter',
        'account_letter_renewal_rel',  # Nombre de la tabla de relación
        'renewal_id',  # Nombre de la columna en la tabla de relación que apunta a este modelo
        'account_letter_id',  # Nombre de la columna en la tabla de relación que apunta al modelo relacionado
        string='Renovaciones',
    )
    renewal_count = fields.Integer(
        string='Cantidad de Renovaciones',
        compute='_compute_renewal_count',
    )
    renewal_parent_id = fields.Many2one(
        'account.letter',
        string='Canje Padre',
    )
    @api.depends('renewal_ids')
    def _compute_renewal_count(self):
        for record in self:
            record.renewal_count = len(record.renewal_ids)
    
    @api.depends('letter_line_ids.is_selected')
    def compute_renewal_protested(self):
        for record in self:
            selected_lines = record.letter_line_ids.filtered('is_selected')
            expiration_dates = selected_lines.mapped('expiration_date')
            if expiration_dates:
                expiration_date = min(expiration_dates)
                difference = (expiration_date - fields.Date.today()).days
                record.is_renewal = difference > 1
                none_protested = all(line.payment_state != 'protested' for line in selected_lines)
                record.is_protested = difference < 1 and none_protested
                has_protested_line = any(line.payment_state == 'protested' for line in selected_lines)
                record.is_refinanced = difference < 1 and has_protested_line
            else:
                record.is_renewal = record.is_protested = record.is_refinanced = False

    #Metodo para renovar las letras
    def action_renewal(self):
        if any(letter.is_selected and letter.payment_state == 'paid' for letter in self.letter_line_ids):
            raise UserError('No puedes renovar letras pagadas.')
        if any(letter.is_selected and letter.payment_state == 'renewed' for letter in self.letter_line_ids):
            raise UserError('Hay letras seleccionadas ya renovadas.')
        #Crear nuevo canje
        selected_letters = self.letter_line_ids.filtered(lambda l: l.is_selected)
        renewal_account_letter = self.env['account.letter'].create({
            'type': self.type,
            'partner_id': self.partner_id.id,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id.id,
            'invoice_date': fields.Date.today(),
            'renewal_parent_id': self.id,
            'invoice_line_ids': [(0, 0, {
                'document_type_id': letter.letter_id.move_id.l10n_latam_document_type_id.id,
                'move_line_id': letter.letter_id.move_id.line_ids.filtered(lambda l: l.name == letter.name).id,
                'amount_total_signed': letter.amount_total,
            }) for letter in selected_letters],
        })
        self.renewal_ids = [(4, renewal_account_letter.id)]
        for letter in selected_letters:
            letter.is_selected = False
            letter.payment_state = 'renewed'
        return {
            'name': 'Renovación de Letras',
            'type': 'ir.actions.act_window',
            'res_model': 'account.letter',
            'res_id': renewal_account_letter.id,
            'view_mode': 'form',
            'target': 'current',
        }
    # ------------------------------------------------------------
    # Protesto y refinanciamiento de las letras
    # ------------------------------------------------------------
    is_protested = fields.Boolean(
        string='Protesto',
        compute='compute_renewal_protested',
    )
    is_refinanced = fields.Boolean(
        string='Refinanciamiento',
        compute='compute_renewal_protested',
    )
    protested_ids = fields.Many2many(
        'account.letter',
        'account_letter_protested_rel',
        'protested_id',
        'account_letter_id',
        string='Refinanciamientos',
    )
    protested_parent_id = fields.Many2one(
        'account.letter',
        string='Canje Padre',
    )
    protested_count = fields.Integer(
        string='Cantidad de Refinanciamientos',
        compute='_compute_protested_count',
    )
    debit_notes_ids = fields.Many2many(
        'account.move',
        string='Notas de Débito',
    )
    count_debit_notes = fields.Integer(
        string='Cantidad de Notas de Débito',
        compute='compute_debit_notes_ids',
    )

    @api.depends('protested_ids')
    def _compute_protested_count(self):
        for record in self:
            record.protested_count = len(record.protested_ids)
    @api.depends('debit_notes_ids')
    def compute_debit_notes_ids(self):
        for record in self:
            record.count_debit_notes = len(record.debit_notes_ids)
    
    #Metodo para protestar las letras
    def action_protest(self):
        if any(letter.is_selected and letter.payment_state == 'paid' for letter in self.letter_line_ids):
            raise UserError('No puedes protestar letras pagadas.')
        # if any(letter.is_selected and letter.payment_state == 'protested' for letter in self.letter_line_ids):
        #     raise UserError('Hay letras seleccionadas ya protestadas.')
        #Crear notas de débito
        selected_letters = self.letter_line_ids.filtered(lambda l: l.is_selected)
        document_type = self.partner_id.l10n_latam_identification_type_id.name
        if document_type == 'RUC':
            document_type = self.env['l10n_latam.document.type'].search([('name', '=', 'Nota de Débito')], limit=1)
        else:
            document_type = self.env['l10n_latam.document.type'].search([('name', '=', 'Nota de Débito Boleta')], limit=1)
        # Si es canje relacionado
        if self.redeemed_type != 'origin':
            condition = self.renewal_parent_id.invoice_line_ids or self.protested_parent_id.invoice_line_ids
        else:
            condition = self.invoice_line_ids
        #Seleccionar un documento del tipo factura cliente o proveedor
        for invoice_line in condition:
            if invoice_line.move_invoice_type in ['out_invoice', 'in_invoice']:
                debit_origin = invoice_line.move_id
                break
        for i in selected_letters:
            debit_note_vals = {
                'invoice_date': fields.Date.today(),
                'partner_id': self.partner_id.id,
                'company_id': self.company_id.id,
                'partner_id': self.partner_id.id,
                'currency_id': self.currency_id.id,
                'letter_id': self.id,
                'letter_line_id': i.id,
                'move_type': self.type,
                'debit_origin_id': debit_origin.id,
                'l10n_latam_document_type_id': document_type.id,
            }
            debit_note = self.env['account.move'].sudo().create(debit_note_vals)
            self.debit_notes_ids = [(4, debit_note.id)]

        #Crear nuevo canje
        protest_account_letter = self.env['account.letter'].create({
            'type': self.type,
            'partner_id': self.partner_id.id,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id.id,
            'invoice_date': fields.Date.today(),
            'protested_parent_id': self.id,
            'invoice_line_ids': [(0, 0, {
                'document_type_id': letter.letter_id.move_id.l10n_latam_document_type_id.id,
                'move_line_id': letter.letter_id.move_id.line_ids.filtered(lambda l: l.name == letter.name).id,
                'amount_total_signed': letter.amount_total,
            }) for letter in selected_letters],
        })
        self.protested_ids = [(4, protest_account_letter.id)]
        for letter in selected_letters:
            letter.is_selected = False
            letter.payment_state = 'protested'
        return {
            'name': 'Protesto de Letras',
            'type': 'ir.actions.act_window',
            'res_model': 'account.letter',
            'res_id': protest_account_letter.id,
            'view_mode': 'form',
            'target': 'current',
        }

    #Metodo para abrir las notas de débito relacionadas
    def action_open_related_debit_notes(self):
        self.ensure_one()
        debit_notes = self.mapped('debit_notes_ids')
        if self.type == 'out_invoice':
            action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        else:
            action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_in_invoice_type")
        if len(debit_notes) > 0:
            action['domain'] = [('id', 'in', debit_notes.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
    
    #Metodo para establecer el tipo de canje
    @api.depends('renewal_parent_id', 'protested_parent_id')
    def _compute_redeemed_type(self):
        for record in self:
            if record.renewal_parent_id:
                record.redeemed_type = 'renewal'
            elif record.protested_parent_id:
                record.redeemed_type = 'protested'
            else:
                record.redeemed_type = 'origin'
    
    #Metodo para cambiar de estado las letras seleccionadas
    def action_change_protested(self):
        for letter in self.letter_line_ids:
            if letter.is_selected:
                letter.payment_state = 'protested'
                letter.is_selected = False

    #Metodo para definir atributos en la pestaña de letras
    # def tree_delete_create(self):
    #     view = self.env.ref('dv_account_letter._account_letter_form').sudo()
    #     doc = etree.XML(view.arch)
    #     for tree in doc.xpath("//tree[@name='letter_line_ids']"):
    #         if self.state == 'draft':
    #             tree.set('create', 'true')
    #             # tree.set('delete', 'true')
    #         else:
    #             tree.set('create', 'false')
    #             # tree.set('delete', 'false')
    #     view.arch = etree.tostring(doc, encoding='unicode')
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'reload',
    #     }

    # def read(self, fields=None, load='_classic_read'):
    #     res = super(AccountLetter, self).read(fields, load)
    #     if len(self) == 1:
    #         self.tree_delete_create()
    #     return res