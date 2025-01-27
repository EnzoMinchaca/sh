from odoo import models, fields, api, _
from odoo.tools.float_utils import float_round


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _l10n_pe_edi_get_edi_values(self, invoice):
        # Sobreescribe el método para modificar la lógica de las cuotas
        self.ensure_one()
        price_precision = self.env['decimal.precision'].precision_get(
            'Product Price')

        def format_float(amount, precision=2):
            ''' Helper to format monetary amount as a string with 2 decimal places. '''
            if amount is None or amount is False:
                return None
            return '%.*f' % (precision, amount)

        # spot = invoice._l10n_pe_edi_get_spot()
        invoice_date_due_vals_list = []
        # first_time = True
        # for rec_line in invoice.line_ids.filtered(lambda l: l.account_type == 'asset_receivable'):
        for rec_line in invoice.line_ids.filtered(lambda l: l.account_type == 'asset_receivable' and not l.l10n_pe_is_spot_line):
            amount = rec_line.amount_currency
            # if spot and first_time:
            #     amount -= spot['spot_amount']
            # first_time = False
            invoice_date_due_vals_list.append({'amount': rec_line.move_id.currency_id.round(amount),
                                               'currency_name': rec_line.move_id.currency_id.name,
                                               'date_maturity': rec_line.date_maturity})
        spot = invoice._l10n_pe_edi_get_spot()
        if not spot:
            total_after_spot = abs(invoice.amount_total)
        else:
            total_after_spot = abs(invoice.amount_total) - spot['spot_amount']
        values = {
            **invoice._prepare_edi_vals_to_export(),
            'spot': spot,
            'total_after_spot': total_after_spot,
            'PaymentMeansID': invoice._l10n_pe_edi_get_payment_means(),
            'is_refund': invoice.move_type in ('out_refund', 'in_refund'),
            'certificate_date': invoice.invoice_date,
            'price_precision': price_precision,
            'format_float': format_float,
            'invoice_date_due_vals_list': invoice_date_due_vals_list,
        }

        # Invoice lines.
        for line_vals in values['invoice_line_vals_list']:
            line = line_vals['line']
            line_vals['price_unit_type_code'] = '01' if not line.currency_id.is_zero(
                line_vals['price_unit_after_discount']) else '02'
            line_vals['price_subtotal_unit'] = float_round(
                line.price_subtotal / line.quantity, precision_digits=price_precision) if line.quantity else 0.0
            line_vals['price_total_unit'] = float_round(
                line.price_total / line.quantity, precision_digits=price_precision) if line.quantity else 0.0

        # Tax details.
        def grouping_key_generator(base_line, tax_values):
            tax = tax_values['tax_repartition_line'].tax_id
            return {
                'l10n_pe_edi_code': tax.tax_group_id.l10n_pe_edi_code,
                'l10n_pe_edi_international_code': tax.l10n_pe_edi_international_code,
                'l10n_pe_edi_tax_code': tax.l10n_pe_edi_tax_code,
            }

        values['tax_details'] = invoice._prepare_edi_tax_details()
        values['tax_details_grouped'] = invoice._prepare_edi_tax_details(
            grouping_key_generator=grouping_key_generator)
        values['isc_tax_amount'] = abs(sum([
            line.amount_currency
            for line in invoice.line_ids.filtered(lambda l: l.tax_line_id.tax_group_id.l10n_pe_edi_code == 'ISC')
        ]))

        return values
