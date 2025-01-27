from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round, float_repr


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends('invoice_line_ids.product_id.l10n_pe_withhold_percentage', 'l10n_latam_document_type_id', 'l10n_pe_edi_is_required', 'partner_id.country_id.code')
    def _compute_l10n_pe_edi_operation_type(self):
        super(AccountMove, self)._compute_l10n_pe_edi_operation_type()
        for record in self:
            pe_partner = record.partner_id.country_id.code == 'PE'
            pe_company = record.l10n_pe_edi_is_required
            is_invoice = record.l10n_latam_document_type_id.code == '01'
            if pe_partner and pe_company and is_invoice:
                spot_percent = max(record.invoice_line_ids.mapped(
                    'product_id.l10n_pe_withhold_percentage'), default=0)
                if spot_percent and record.amount_total_signed > 700.0:
                    record.l10n_pe_edi_operation_type = '1001'

    def _l10n_pe_edi_get_spot(self):
        if self.amount_total_signed > 700.0:
            res = super(AccountMove, self)._l10n_pe_edi_get_spot()
            if res:
                res['Amount'] = self.l10n_pe_spot_amount_currency
                res['spot_amount'] = self.l10n_pe_spot_amount
                res['AmountToPay'] = self.amount_total - self.l10n_pe_spot_amount
        else:
            res = {}
        return res

    # ===== Integración con módulo de coutas: dv_l10n_pe_edi_date_due_list =====
    def _l10n_pe_edi_is_spot_or_withholding_installed(self):
        # Override
        return True

    def _l10n_pe_edi_net_amount_due_lines(self):
        res = super(AccountMove, self)._l10n_pe_edi_net_amount_due_lines()
        res = res.filtered(lambda l: abs(l.balance) != self.l10n_pe_spot_amount_currency)
        return res