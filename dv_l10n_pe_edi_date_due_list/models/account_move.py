from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _l10n_pe_edi_is_spot_or_withholding_installed(self):
        """
        Retorna True si los módulos dv_l10n_pe_edi_detraction o dv_l10n_pe_edi_retention
        están instalados en el sistema
        """
        return False
    
    def _l10n_pe_edi_net_amount_due_lines(self):
        """
        Para ser sobreescrito en los módulos dv_l10n_pe_edi_detraction o dv_l10n_pe_edi_retention
        - Retorna los apuntes contables de la factura que son de tipo 'asset_receivable'
        """
        net_amount_due_lines = self.line_ids.filtered(lambda l: l.account_type == 'asset_receivable')
        return net_amount_due_lines
    
    def _l10n_pe_edi_get_dues(self):
        """
        Retorna las cuotas de la factura
        - En este módulo tiene el comportamiento de odoo nativo (l10n_pe_edi), sin embargo
            se usará en módulos como dv_l10n_edi_detractions y dv_l10n_pe_edi_retentions para
            considerar el monto de la detracción y retención en la cuota
        """
        invoice_date_due_vals_list = []
        if self._l10n_pe_edi_is_spot_or_withholding_installed():
            net_amount_due_lines = self._l10n_pe_edi_net_amount_due_lines()
            for rec_line in net_amount_due_lines:
                invoice_date_due_vals_list.append({
                    'amount': rec_line.move_id.currency_id.round(rec_line.amount_currency),
                    'currency_name': rec_line.move_id.currency_id.name,
                    'date_maturity': rec_line.date_maturity
                })
        else:
            spot = self._l10n_pe_edi_get_spot()
            first_time = True
            for rec_line in self.line_ids.filtered(lambda l: l.account_type == 'asset_receivable'):
                amount = rec_line.amount_currency
                if spot and first_time:
                    amount -= spot['spot_amount']
                first_time = False
                invoice_date_due_vals_list.append({
                    'amount': rec_line.move_id.currency_id.round(amount),
                    'currency_name': rec_line.move_id.currency_id.name,
                    'date_maturity': rec_line.date_maturity
                })
        return invoice_date_due_vals_list

    def _l10n_pe_edi_net_amount(self):
        """
        Retorna el monto neto de la factura
        - En este módulo tiene el comportamiento de odoo nativo (l10n_pe_edi), sin embargo
            se usará en módulos como dv_l10n_edi_detractions y dv_l10n_pe_edi_retentions para
            considerar el monto de la detracción y retención en la cuota
        """
        spot = self._l10n_pe_edi_get_spot()
        if not spot:
            total_after_spot = abs(self.amount_total)
        else:
            total_after_spot = abs(self.amount_total) - spot['spot_amount']
        return total_after_spot
