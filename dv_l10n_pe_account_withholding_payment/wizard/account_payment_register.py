from odoo import _, api, fields, models
from odoo.exceptions import UserError

"""
==============================================================
Tratamiento de pagos de detracción y retención de proveedores
==============================================================

Condiciones para que se aplique retención a una factura que está siendo pagada:
-------------------------------------------------------------------------------
- La compañía es agente de retención
- El proveedor es de Perú
- El proveedor no es agente de retención
- El proveedor no es buen contribuyente
- El monto del pago es mayor a 700 PEN
- El porcentaje de detracción de la factura es menor al porcentaje de retención (implícitamente considera los casos que no tienen detracción)

Ejemplo con casos prácticos:
----------------------------

Compañía:
- Agente de retención: Si

Proveedor #1
- País: Perú
- Agente de retención: No
- Buen contribuyente: No

Factura #1
- Proveedor: Proveedor #1
- Importe total: 1000 PEN
- Porcentaje de detracción: 0%
- Detracción: 0 PEN
                
Factura #2
- Proveedor: Proveedor #1
- Importe total: 1000 PEN
- Porcentaje de detracción: 10%
- Detracción: 100 PEN


Caso #1: Pago total de Factura #1
----------------------------------
- Paso 1. Registro de la factura
    Código  |   Cuenta              |   Debe    |   Haber
    --------+-----------------------+-----------+---------
    4010    |	IGV                 |   847.46  |   0
    6011	|   Ret x emitir        |   152.54  |   0
    4211	|   Cuentas x pagar	    |   0       |   1000
    
- Paso 2. Pago de 1000 PEN
    Código  |   Cuenta              |   Debe    |   Haber
    --------+-----------------------+-----------+---------
    4211	|   Cuentas x pagar	    |   1000    |   0
    1041    |	Pagos pendientes    |   0       |   970
    4212	|   Ret x emitir        |   0       |   30
                    
- Paso 3. Emisión de comprobante de retención del pago
    Código  |   Cuenta              |   Debe    |   Haber
    --------+-----------------------+-----------+---------
    4212	|   Ret x emitir        |   30      |   0
    4011	|   Retenciones x pagar |   0       |   30

- Paso 4. Pago de todos los comprobantes de retención del mes
    Código  |   Cuenta              |   Debe    |   Haber
    --------+-----------------------+-----------+---------
    4011	|   Retenciones	x pagar |   30      |   0
    1041	|   Banco               |   0       |   30


Caso #2: Pago total de Factura #2
----------------------------------
- Paso 1. Registro de la factura
    Código  |   Cuenta              |   Debe    |   Haber
    --------+-----------------------+-----------+---------
    4010    |	IGV                 |   847.46  |   0
    6011	|   Ret x emitir        |   152.54  |   0
    4212	|   Detracciones x pagar|   0       |   100
    4211	|   Cuentas x pagar	    |   0       |   900
    
- Paso 2. Pago del monto neto 900 PEN (como el porcentaje de detracción es menor al porcentaje de retención, no se aplica retención)
    Código  |   Cuenta              |   Debe    |   Haber
    --------+-----------------------+-----------+---------
    4211	|   Cuentas x pagar	    |   900     |   0
    1041    |	Pagos pendientes    |   0       |   900
                    
- Paso 3. Pago de la detracción 100 PEN
    Código  |   Cuenta              |   Debe    |   Haber
    --------+-----------------------+-----------+---------
    4212	|   Detracciones x pagar|   100     |   0
    1041    |	Pagos pendientes    |   0       |   100
"""


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'


    # ============================== WITHHOLDING ==============================
    l10n_pe_withholding_subject_invoice_ids = fields.Many2many(
        'account.move', 'account_payment_register_withholding_subject_invoice_rel', 'account_payment_register_id', 'account_move_id',
        string='Facturas sujetas a retención', compute='_compute_l10n_pe_withholding_subject_invoice', store=True)
    withholding_tax_table_id = fields.Many2one(
        'l10n_pe.withholding.code', string='Codigo de retención', compute='_compute_l10n_pe_withholding_subject_invoice', store=True, readonly=False)
    account_withholding_percent = fields.Float(
        string='Porcentaje de retención', related='withholding_tax_table_id.percentage', readonly=False)

    l10n_pe_pay_withholding = fields.Boolean(
        string='Es pago de retención', default=False)
    @api.depends('line_ids')
    def _compute_l10n_pe_withholding_subject_invoice(self):
        """
        En un pago se aplica retención si:
        Para pagos de clientes:
        - La empresa no es agente de retención
        - La empresa no es buen contribuyente
        - El cliente es de Perú
        - El cliente es agente de retención
        - El monto del pago es mayor a 700 PEN
        Para pagos de proveedores:
        - La empresa es agente de retención
        - El proveedor es de Perú
        - El proveedor no es agente de retención
        - El proveedor no es buen contribuyente
        - El monto del pago es mayor a 700 PEN
        """
        for record in self:
            l10n_pe_withholding_subject_invoice_ids = self.env['account.move']
            withholding_tax_table_id = False
            account_withholding_percent = 0
            if record.company_id.country_id.code == 'PE' and record.partner_id.country_id.code == 'PE' and (abs(record.source_amount) >= 700 or self.l10n_pe_pay_withholding):
                withholding_tax_table_id = self.env['l10n_pe.withholding.code'].search([
                ], limit=1)
                account_withholding_percent = withholding_tax_table_id.percentage
                if record.payment_type == 'inbound' and not record.company_id.l10n_pe_is_retention_agent:
                    # Cobros de facturas de clientes
                    withholding_domain = [
                        ('move_id.partner_id.l10n_pe_is_retention_agent', '=', True)]
                elif record.payment_type == 'outbound' and record.company_id.l10n_pe_is_retention_agent:
                    # Pagos de facturas de proveedores
                    withholding_domain = [('move_id.partner_id.l10n_pe_is_retention_agent', '=', False)]
                else:
                    withholding_domain = [('partner_id', '=', 0)]
                l10n_pe_withholding_subject_invoice_ids = record.line_ids.filtered_domain(
                    withholding_domain).mapped('move_id')
            record.l10n_pe_withholding_subject_invoice_ids = l10n_pe_withholding_subject_invoice_ids
            record.withholding_tax_table_id = withholding_tax_table_id

    l10n_pe_withholding_amount_currency = fields.Monetary(
        string='Monto de retención en moneda de la empresa', currency_field='company_currency_id', compute='_compute_l10n_pe_withholding_amount', store=True)
    l10n_pe_withholding_amount = fields.Monetary(
        string='Monto de retención', currency_field='currency_id', compute='_compute_l10n_pe_withholding_amount', store=True)

    @api.depends('account_withholding_percent', 'l10n_pe_withholding_subject_invoice_ids.amount_total', 'l10n_pe_withholding_subject_invoice_ids.amount_total_signed')
    def _compute_l10n_pe_withholding_amount(self):
        for record in self:
            account_withholding_percent = record.account_withholding_percent / 100
            l10n_pe_withholding_amount_currency = sum(
                record.l10n_pe_withholding_subject_invoice_ids.mapped('amount_total')) * account_withholding_percent
            l10n_pe_withholding_amount = abs(sum(
                record.l10n_pe_withholding_subject_invoice_ids.mapped('amount_total_signed'))) * account_withholding_percent
            record.l10n_pe_withholding_amount_currency = l10n_pe_withholding_amount_currency
            record.l10n_pe_withholding_amount = l10n_pe_withholding_amount

    @api.depends('l10n_pe_withholding_amount')
    def _compute_group_payment(self):
        """
        Los pagos se deben agrupar si:
        - El pago es sujeto a retención
        - Si es un pago por el total de facturas con detracción
        """
        super(AccountPaymentRegister, self)._compute_group_payment()
        for record in self:
            if record.l10n_pe_withholding_amount > 0:
                record.group_payment = True

    @api.depends('l10n_pe_withholding_amount_currency', 'payment_method_line_id')
    def _compute_amount(self):
        """
        El monto del pago es:
        Total de facturas - Monto de detracción - Monto de retención
        Si se paga solo detracción, el monto del pago es el monto de detracción
        """
        super(AccountPaymentRegister, self)._compute_amount()
        for record in self:
            # TODO agregar validaciones cuando es pago en dolares o factura en dolares
            current_amount = record.amount
            payment_method_code = record.payment_method_line_id.payment_method_id.code
        
            if record.currency_id != record.company_currency_id:
                amount = current_amount - record.l10n_pe_withholding_amount_currency
            else:
                amount = current_amount - record.l10n_pe_withholding_amount
            
            record.amount = amount

    @api.depends('l10n_pe_withholding_subject_invoice_ids')
    def _compute_payment_difference(self):
        """
        Si el pago es sujeto a retención, no debe mostrar la diferencia de pago
        """
        super(AccountPaymentRegister, self)._compute_payment_difference()
        for record in self:
            if record.l10n_pe_withholding_subject_invoice_ids:
                record.payment_difference = 0.0

    def _get_withholding_journal_id(self):
        self.ensure_one()
        """
        Cuando realizamos un pago a un proveedor (outbound):
        -El diario de retención debe ser de tipo in_withhold (Retenciones de compras)
        Cuando realizamos un pago de un cliente (inbound):
        -El diario de retención debe ser de tipo out_withhold (Retenciones de ventas)
        """
        AccountJournal = self.env['account.journal']
        if self.payment_type == 'inbound':
            withholding_journal_id = AccountJournal.search(
                [('company_id', '=', self.company_id.id),
                 ('type', '=', 'purchase'),
                 ('l10n_latam_use_documents', '=', True),
                 ('l10n_pe_is_withhold_journal', '=', True)], limit=1).id
        elif self.payment_type == 'outbound':
            withholding_journal_id = AccountJournal.search(
                [('company_id', '=', self.company_id.id),
                 ('type', '=', 'sale'),
                 ('l10n_latam_use_documents', '=', True),
                 ('l10n_pe_is_withhold_journal', '=', True)], limit=1).id
        if not withholding_journal_id:
            raise UserError(
                "Debe configurar un diario de retención desde Contabilidad > Configuración > Diarios")
        return withholding_journal_id

    def _prepare_withholding_lines(self):
        # TODO verificar que el monto de la retencion de una factura en dolares
        # sea al tipo de cambio de la fecha del pago
        # TODO se puede hacer pagos parciales a facturas sujetas a retencion?
        # Como se registraria la retencion en el asiento de pago?
        withholding_lines = []
        for move_id in self.l10n_pe_withholding_subject_invoice_ids.line_ids.filtered(lambda line: line.id in self.line_ids.ids).move_id:
            # Monto de retencion en moneda del pago
            withholding_amount_currency = move_id.amount_total * \
                self.account_withholding_percent / 100

            withholding_account_id = self.company_id.withholding_account_id
            if not withholding_account_id:
                raise UserError(
                    "Debe configurar una cuenta de retención desde Contabilidad > Configuración > Ajustes")

            line_data = {
                'partner_id': self.partner_id.id,
                'currency_id': self.l10n_pe_withholding_subject_invoice_ids.currency_id.id, # TODO validar este requerimiento
                'display_type': 'payment_term',
            }
            withholding_lines += [(0, 0, {
                **line_data,
                'name': f'Retención de {move_id.name}',
                'account_id': withholding_account_id.id,
                'price_unit': withholding_amount_currency,
                'quantity': 1,
                'tax_ids': False,
                'l10n_pe_withhold_invoice_id': move_id.id,
                'display_type': 'product',
            })]
        return withholding_lines

    l10n_pe_withholding_document_number = fields.Char(
        string='Número de comprobante de retención')

    def _create_withholding_move(self):
        self.ensure_one()
        withholding_invoice_names = self.l10n_pe_withholding_subject_invoice_ids.mapped(
            'name')
        if self.payment_type == 'inbound':
            move_type = 'in_invoice'
        elif self.payment_type == 'outbound':
            move_type = 'out_invoice'
        data = {
            'move_type': move_type,
            'ref': f"Retención de {withholding_invoice_names}",
            'journal_id': self._get_withholding_journal_id(),
            'l10n_latam_document_type_id': self.env.ref('l10n_pe.document_type20').id,
            'l10n_latam_document_number': self.l10n_pe_withholding_document_number,
            'date': self.payment_date,
            'invoice_date': self.payment_date,
            'invoice_date_due': self.payment_date,
            'invoice_date': self.payment_date,
            'company_id': self.company_id.id,
            'partner_id': self.partner_id.id,
            'currency_id': self.l10n_pe_withholding_subject_invoice_ids.currency_id.id, # TODO validar este requerimiento
            'line_ids': self._prepare_withholding_lines(),
        }
        withholding_account_move_id = self.env['account.move'].create(data)
        withholding_account_move_id._l10n_pe_configure_withholding_document_lines()
        withholding_account_move_id.action_post()
        self._reconcile_withholding(withholding_account_move_id)

    def _reconcile_withholding(self, to_process):
        """
        Concilia la linea de contrapatida del compronbante de retención con las lineas de cada factura relacionada      
        """
        reconcile_domain = [('account_id.reconcile', '=', True),
                            ('account_id.account_type', 'in', ['asset_receivable', 'liability_payable'])]

        for withhold_line_id in to_process.line_ids.filtered_domain(reconcile_domain):
            withholding_invoice_id = withhold_line_id.l10n_pe_withhold_invoice_id
            withholding_amount_currency = withholding_invoice_id.amount_total * \
                self.account_withholding_percent / 100
            invoice_line_id = withholding_invoice_id.line_ids.filtered_domain(
                reconcile_domain + ['|', ('balance', '=', withholding_amount_currency), ('balance', '=', -1 * withholding_amount_currency)])
            if not invoice_line_id:
                invoice_line_id = withholding_invoice_id.line_ids.filtered_domain(
                    reconcile_domain)
            reconcile_lines = invoice_line_id + withhold_line_id
            reconcile_lines.reconcile()

    def _create_payments(self):
        if self.l10n_pe_withholding_amount and self.l10n_pe_pay_withholding:
            # Crea primero el asiento de retención para ser conciliados antes de crear el pago
            # TODO Por requerimiento de un cliente se agrego que se cree un comprobante de retencion por moneda
            # Es decir, si la factura es en dolares, que se cree el comprobante de retencion en dolares
            more_than_one_currency = len(self.l10n_pe_withholding_subject_invoice_ids.mapped('currency_id')) > 1
            if more_than_one_currency:
                raise UserError(
                    "No se puede generar un comprobante de retención para facturas en diferentes monedas, por favor seleccione facturas de una misma moneda")
            self._create_withholding_move()
        else:
            # Si no marca la opción de pagar retención, se paga solo el monto neto
            res = super(AccountPaymentRegister, self)._create_payments()
        return res
