from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import date

class AccountMove(models.Model):
    _inherit = 'account.move'

    visible = fields.Boolean(help='Visibilidad del campo amount_retention_optional', default=False)

    amount_retention = fields.Monetary(string='Monto de retención', 
        compute='_compute_amount_retention', store=True
    )

    amount_retention_optional = fields.Monetary(
        string='Monto de retención a pagar',
        compute='_compute_amount_retention',
        store=True,
        currency_field='company_currency_id'
    )

    percent_retention = fields.Float(string='Porcentaje de retención (%)', 
        compute='_compute_percent_retention', store=True, readonly="0"
    )

    status_amount_retention = fields.Boolean(default=False)

    status_retention_validate = fields.Boolean(default=False)

    @api.depends('l10n_pe_is_subject_to_withholding')
    def _compute_percent_retention(self):
        for record in self:
            if record.l10n_pe_is_subject_to_withholding:
                record.percent_retention = record.l10n_pe_withholding_code_percentage
            else:
                percent = self.env['l10n_pe.withholding.code'].search([], order='id desc', limit=1).percentage
                record.percent_retention = percent
    
    def update_exchange_rate(self):
        return

    @api.depends('l10n_pe_withholding_amount_currency', 'l10n_pe_is_subject_to_withholding')
    def _compute_amount_retention(self):

        for record in self:
            percent = record.percent_retention / 100

            if record.status_retention_validate == False:
                record.amount_retention = record.amount_total * percent

    def set_payment_type_and_register_payment(self):

        selected_invoices = self.env['account.move'].browse(self.env.context.get('active_ids', []))

        var = self.env['account.payment.date'].create({
            'l10n_pe_withholding_subject_invoice_ids': selected_invoices.ids
        })
        
        return {
            'name': 'Registrar Fecha de Pago',
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment.date',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': var.id,
            'target': 'new',
        }

    

    def _l10n_pe_is_withholding(self):
        return self.country_code == 'PE' and self.journal_id.l10n_pe_is_withhold_journal
    
    def _l10n_pe_configure_withholding_document_lines(self, invoice_ids = [], payment_difference_handling = '', payment_difference_calculate = 0.0, amount_total_final= 0.0):

        amount_retentions = []
        for retention in invoice_ids:
            amount_retentions.append(retention.amount_retention_optional)

        for record in self:
            if record._l10n_pe_is_withholding():
                if record.move_type == 'in_invoice':
                    partner_account_id = record.partner_id.property_account_receivable_id
                elif record.move_type == 'out_invoice':
                    partner_account_id = record.partner_id.property_account_payable_id
                    
                new_lines = []
                first_line = True
                partner_line_id = record.line_ids.filtered_domain(
                    [('account_id.account_type', 'in', ['liability_payable', 'asset_receivable'])])
                index = 0
                for line in record.line_ids.filtered_domain([('l10n_pe_withhold_invoice_id', '!=', False)]):

                    if first_line:
                        update_line = {
                            'account_id': partner_account_id.id,
                            'amount_currency': amount_retentions[index] * (-1 if record.move_type == 'in_invoice' else 1),
                            'l10n_pe_withhold_invoice_id': line.l10n_pe_withhold_invoice_id.id,
                            }
                        first_line = False
                    else:
                        new_lines.append((0, 0, {
                            'name': line.name,
                            'account_id': partner_account_id.id,
                            'currency_id': line.currency_id.id,

                            'amount_currency': amount_retentions[index] * (-1 if record.move_type == 'in_invoice' else 1),

                            'partner_id': line.partner_id.id,
                            'display_type': 'payment_term',
                            'l10n_pe_withhold_invoice_id': line.l10n_pe_withhold_invoice_id.id,
                            'date_maturity': line.date_maturity,
                            'date': line.date,
                        }))
                    index += 1
                
                record.line_ids = [
                        (1, partner_line_id.id, update_line)] + new_lines

    def get_exchange_rate_usd_to_pen(self):
        currency_usd = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        if not currency_usd:
            raise UserError('No se encontró la moneda USD.')

        currency_pen = self.env['res.currency'].search([('name', '=', 'PEN')], limit=1)
        if not currency_pen:
            raise UserError('No se encontró la moneda PEN.')
        
        exchange_rate = self.env['res.currency.rate'].search([
            ('currency_id', '=', currency_usd.id),
            ('name', '<=', date.today())
        ], order='name desc', limit=1)
        if not exchange_rate:
            raise UserError('No se encontró un tipo de cambio para USD en la fecha de hoy.')

        return exchange_rate.inverse_company_rate