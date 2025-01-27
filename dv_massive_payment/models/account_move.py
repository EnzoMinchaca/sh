from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import date

class AccountMove(models.Model):
    _inherit = 'account.move'

    currency_id_to_payment = fields.Many2one(
        comodel_name='res.currency',
        string='Currency payment',
        default=lambda self: self.env.company.currency_id,
        store=True
    )

    amount_to_payment = fields.Monetary(
        string='Monto a pagar',
        store=True,
        currency_field='currency_id_to_payment'
    )

    @api.depends('amount_total')
    def _compute_amount_to_payment(self):
        for record in self:
            record.amount_to_payment = record.amount_total

    def register_payment(self):
        selected_invoices = self.env['account.move'].browse(self.env.context.get('active_ids', []))

        var = self.env['massive.payment.register'].create({
            'list_invoices_ids': selected_invoices.ids
        })
        
        return {
            'name': 'Registrar Pago',
            'type': 'ir.actions.act_window',
            'res_model': 'massive.payment.register',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': var.id,
            'target': 'new',
        }
    
    # def _l10n_pe_configure_payment_document_lines(self, invoice_ids = [], payment_difference_handling = '', payment_difference_calculate = 0.0, amount_total_final= 0.0):

        # amount_retentions = []
        # for retention in invoice_ids:
        #     amount_retentions.append(retention.amount_retention_optional)

        # for record in self:
        #     if record._l10n_pe_is_withholding():
        #         if record.move_type == 'in_invoice':
        #             partner_account_id = record.partner_id.property_account_receivable_id
        #         elif record.move_type == 'out_invoice':
        #             partner_account_id = record.partner_id.property_account_payable_id
                    
        #         new_lines = []
        #         first_line = True
        #         partner_line_id = record.line_ids.filtered_domain(
        #             [('account_id.account_type', 'in', ['liability_payable', 'asset_receivable'])])
        #         index = 0
        #         for line in record.line_ids.filtered_domain([('l10n_pe_withhold_invoice_id', '!=', False)]):

        #             if first_line:
        #                 update_line = {
        #                     'account_id': partner_account_id.id,
        #                     'amount_currency': amount_retentions[index] * (-1 if record.move_type == 'in_invoice' else 1),
        #                     'l10n_pe_withhold_invoice_id': line.l10n_pe_withhold_invoice_id.id,
        #                     }
        #                 first_line = False
        #             else:
        #                 new_lines.append((0, 0, {
        #                     'name': line.name,
        #                     'account_id': partner_account_id.id,
        #                     'currency_id': line.currency_id.id,

        #                     'amount_currency': amount_retentions[index] * (-1 if record.move_type == 'in_invoice' else 1),

        #                     'partner_id': line.partner_id.id,
        #                     'display_type': 'payment_term',
        #                     'l10n_pe_withhold_invoice_id': line.l10n_pe_withhold_invoice_id.id,
        #                     'date_maturity': line.date_maturity,
        #                     'date': line.date,
        #                 }))
        #             index += 1
                
        #         record.line_ids = [
        #                 (1, partner_line_id.id, update_line)] + new_lines