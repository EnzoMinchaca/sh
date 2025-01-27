from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    withholding_group_visible = fields.Boolean(string='Grupo de retención visible', compute='_compute_withholding_group_visible',
                                               store=True, help='Campo técnico para mostrar la página de retención en el formulario de factura')

    @api.depends('partner_id.l10n_pe_is_retention_agent', 'partner_id.country_id.code', 'company_id.l10n_pe_is_retention_agent', 'company_id.country_id.code', 'move_type')
    def _compute_withholding_group_visible(self):
        """
        La página de retención es visible si:
        Para facturas de venta:
        - La empresa no es agente de retención
        - El cliente es de Perú
        - El cliente es agente de retención
        """
        for record in self:
            withholding_group_visible = False
            if record.company_id.country_id.code == 'PE' and record.partner_id.country_id.code == 'PE':
                if record.move_type == 'out_invoice':
                    if not record.company_id.l10n_pe_is_retention_agent and record.partner_id.l10n_pe_is_retention_agent:
                        withholding_group_visible = True
            record.withholding_group_visible = withholding_group_visible

    l10n_pe_is_subject_to_withholding = fields.Boolean(
        string='Sujeto a Retención', compute='_compute_is_subject_to_withholding', store=True, readonly=False)

    @api.depends('withholding_group_visible', 'amount_total_signed', 'move_type', 'l10n_pe_edi_operation_type')
    def _compute_is_subject_to_withholding(self):
        """
        Una factura por sí misma es sujeta a retención si:
        Para facturas de venta:
        - La empresa no es agente de retención
        - El cliente es de Perú
        - El cliente es agente de retención
        - El monto total en soles es mayor a 700
        - El porcentaje de retención es menor al porcentaje de retención
        """
        for record in self:
            l10n_pe_is_subject_to_withholding = False
            if record.withholding_group_visible and abs(record.amount_total_signed) > 700 and record.l10n_pe_edi_operation_type == '0101':
                l10n_pe_is_subject_to_withholding = True
            record.l10n_pe_is_subject_to_withholding = l10n_pe_is_subject_to_withholding

    withholding_tax_table_id = fields.Many2one(
        'l10n_pe.withholding.code', string='Codigo de retención', compute='_compute_withholding_tax_table_id', store=True, readonly=False)

    l10n_pe_withholding_code_percentage = fields.Float(
        string='Porcentaje de retención', related='withholding_tax_table_id.percentage', readonly=False)

    @api.depends('l10n_pe_is_subject_to_withholding')
    def _compute_withholding_tax_table_id(self):
        for record in self:
            if record.l10n_pe_is_subject_to_withholding:
                withholding_tax_table_id = self.env['l10n_pe.withholding.code'].search([
                ], limit=1)
            else:
                withholding_tax_table_id = False
            record.withholding_tax_table_id = withholding_tax_table_id

    l10n_pe_withholding_amount = fields.Monetary(
        string='Monto de retención', currency_field='currency_id', compute='_compute_withholding_amount', store=True)
    l10n_pe_withholding_amount_signed = fields.Monetary(
        string='Monto de retención en moneda de la empresa con signo', currency_field='company_currency_id', compute='_compute_withholding_amount', store=True)
    l10n_pe_withholding_amount_currency = fields.Monetary(
        string='Monto de retención en moneda de la empresa', currency_field='company_currency_id', compute='_compute_withholding_amount', store=True)

    @api.depends('amount_total', 'l10n_pe_withholding_code_percentage', 'amount_total_signed')
    def _compute_withholding_amount(self):
        for record in self:
            if record.l10n_pe_withholding_code_percentage:
                withholding_percentage = record.l10n_pe_withholding_code_percentage / 100
                l10n_pe_withholding_amount = record.amount_total * withholding_percentage
                l10n_pe_withholding_amount_signed = record.amount_total_signed * withholding_percentage
                l10n_pe_withholding_amount_currency = abs(
                    l10n_pe_withholding_amount_signed)
                record.write({
                    'l10n_pe_withholding_amount': l10n_pe_withholding_amount,
                    'l10n_pe_withholding_amount_signed': l10n_pe_withholding_amount_signed,
                    'l10n_pe_withholding_amount_currency': l10n_pe_withholding_amount_currency,
                })
            else:
                record.l10n_pe_withholding_amount = 0
                record.l10n_pe_withholding_amount_signed = 0
                record.l10n_pe_withholding_amount_currency = 0

    @api.onchange('l10n_pe_edi_operation_type')
    def _onchange_l10n_pe_edi_operation_type(self):
        if self.l10n_pe_edi_operation_type in ['1001', '1002']:
            self.l10n_pe_is_subject_to_withholding = False
            self.withholding_tax_table_id = False

    @api.onchange('l10n_pe_is_subject_to_withholding')
    def _onchange_is_subject_to_withholding(self):
        if self.l10n_pe_is_subject_to_withholding:
            self.l10n_pe_edi_operation_type = '0101'

    def _l10n_pe_edi_get_retention(self):
        percentage = self.l10n_pe_withholding_code_percentage
        if self.amount_total_signed < 700.0 or not percentage or self.move_type == 'out_refund':
            return {}

        return {
            'ID': 'Retención',
            'PaymentMeansID': self.withholding_tax_table_id.code,
            # 'PaymentMeansCode': '999',
            'retention_amount': self.l10n_pe_withholding_amount,
            'Amount': self.l10n_pe_withholding_amount_currency,
            'PaymentPercent': percentage,
        }

    def _post(self, soft=True):
        for move in self:
            if move.l10n_pe_is_subject_to_withholding:
                move.sudo()._l10n_pe_configure_withholding_lines()
        res = super(AccountMove, self)._post(soft=soft)
        return res

    def _l10n_pe_configure_withholding_lines(self):
        """
        Modifica la configuracion del account.payment.term temporalmente para que la primera linea de deuda tenga el monto de la retencion
        y las siguientes lineas sumen el monto neto de la factura.
        """
        if self.invoice_payment_term_id:
            payment_term = self.invoice_payment_term_id
            # Valida que no haya lineas de tipo fixed
            if payment_term.line_ids.filtered_domain([('value', '=', 'fixed')]):
                raise UserError(
                    "No se puede configurar la retención porque el plazo de pago tiene lineas de tipo fijo.")
            # La primera linea es del plazo de pago es la retencion
            new_payment_term_lines = [(5, 0, 0), (0, 0, {
                'value': 'fixed',
                'value_amount': self.l10n_pe_withholding_amount,
                'l10n_pe_is_withholding_term_line': True,
                'nb_days': 1,
            })]
            old_payment_term_lines = [(5, 0, 0)]
            new_payment_term_lines = [(5, 0, 0), (0, 0, {
                'value': 'fixed',
                'value_amount': self.l10n_pe_withholding_amount,
                'l10n_pe_is_withholding_term_line': True,
                'nb_days': 1,
            })]
            net_amount = self.amount_total_signed - self.l10n_pe_withholding_amount_signed
            # Reparte el monto neto en las siguientes lineas
            for line in payment_term.line_ids:
                value = {
                    'nb_days': line.nb_days,
                    'value': 'percent',
                    'value_amount': line.value_amount,
                }
            
                old_payment_term_lines.append((0, 0, value))
                new_payment_term_lines.append((0, 0, value))

            payment_term.write({'line_ids': new_payment_term_lines})
            self._compute_needed_terms()
            self._compute_tax_totals()
            self._compute_show_payment_term_details()
            payment_term.write({'line_ids': old_payment_term_lines})
        else:
            # Si no hay plazo de pago, utiliza el campo de fecha de vencimiento para crear uno temporal
            if not self.invoice_date_due or not self.invoice_date:
                raise UserError(
                    "No se puede configurar la retención porque no hay fecha de vencimiento o fecha de factura.")
            days_to_pay = (self.invoice_date_due - self.invoice_date).days if self.invoice_date_due != self.invoice_date else 1
            AccountPaymentTerm = self.env['account.payment.term']
            payment_term = AccountPaymentTerm.create({
                'name': self.invoice_date_due.strftime('%d/%m/%Y'),
                'display_on_invoice': False,
                'note': f'Plazo de pago temporal para la retención de la factura {self.name}',
                'line_ids': [(0, 0, {
                    'value': 'fixed',
                    'value_amount': self.l10n_pe_withholding_amount,
                    'l10n_pe_is_withholding_term_line': True,
                    'nb_days': days_to_pay + 1,
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

    def button_draft(self):
        super(AccountMove, self).button_draft()
        if self.l10n_pe_is_subject_to_withholding and not self.invoice_payment_term_id.active:
            self.invoice_payment_term_id = False

    # ===== Integración con módulo de coutas: dv_l10n_pe_edi_date_due_list =====
    def _l10n_pe_edi_is_spot_or_withholding_installed(self):
        # Override
        return True

    def _l10n_pe_edi_net_amount_due_lines(self):
        res = super(AccountMove, self)._l10n_pe_edi_net_amount_due_lines()
        res = res.filtered(lambda l: abs(l.amount_currency) !=
                           self.l10n_pe_withholding_amount)
        return res

    def _l10n_pe_edi_net_amount(self):
        """
        Retorna el monto neto de la factura
        - En este módulo tiene el comportamiento de odoo nativo (l10n_pe_edi), sin embargo
            se usará en módulos como dv_l10n_edi_detractions y dv_l10n_pe_edi_retentions para
            considerar el monto de la detracción y retención en la cuota
        """
        total_after_spot = super(AccountMove, self)._l10n_pe_edi_net_amount()
        withholding = self._l10n_pe_edi_get_retention()
        if withholding:
            total_after_spot -= withholding['retention_amount']
        return total_after_spot