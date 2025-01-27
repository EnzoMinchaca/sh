from odoo import models, api, _
from odoo.tools.float_utils import float_round
import logging
_logger = logging.getLogger(__name__)

class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _l10n_pe_edi_get_edi_values(self, invoice):
        """
        Sobreescribe el método de odoo nativo (l10n_pe_edi) opara modificar
        la lógica del cálculo de los datos de la factura para que utilice
        los métodos _l10n_pe_edi_get_dues y _l10n_pe_edi_net_amount definidos
        en este módulo.
        """
        self.ensure_one()
        price_precision = self.env['decimal.precision'].precision_get(
            'Product Price')

        def format_float(amount, precision=2):
            ''' Helper to format monetary amount as a string with 2 decimal places. '''
            if amount is None or amount is False:
                return None
            return '%.*f' % (precision, amount)

        invoice_date_due_vals_list = invoice._l10n_pe_edi_get_dues()
        spot = invoice._l10n_pe_edi_get_spot()
        total_after_spot = invoice._l10n_pe_edi_net_amount()
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
        _logger.info('_l10n_pe_edi_get_edi_values')
        _logger.info('values: %s', values)
        return values
