from odoo import models, api, _


class AccountEdiXmlUBLPE(models.AbstractModel):
    _inherit = 'account.edi.xml.ubl_pe'

    def _get_document_allowance_charge_vals_list(self, invoice):
        vals_list = super()._get_document_allowance_charge_vals_list(invoice)
        if invoice.l10n_pe_is_subject_to_withholding:
            vals_list.append({
                'charge_indicator': 'false',
                'allowance_charge_reason_code': '62',
                'multiplier_factor': invoice.l10n_pe_withholding_code_percentage / 100,
                'amount': invoice.l10n_pe_withholding_amount,
                'base_amount': invoice.amount_total,
                'currency_name': invoice.currency_id.name,
                'currency_dp': invoice.currency_id.decimal_places,
            })
        return vals_list

    def _export_invoice_vals(self, invoice):
        """
        Disminuye el monto de A
        """
        vals = super()._export_invoice_vals(invoice)
        withholding_amount = invoice.l10n_pe_withholding_amount
        if vals['vals']['monetary_total_vals']['allowance_total_amount']:
            vals['vals']['monetary_total_vals']['allowance_total_amount'] -= withholding_amount
        return vals