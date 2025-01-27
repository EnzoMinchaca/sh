from odoo import _, api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    def _l10n_pe_is_withholding(self):
        return self.country_code == 'PE' and self.journal_id.l10n_pe_is_withhold_journal
    
    def _l10n_pe_configure_withholding_document_lines(self):
        """
        Se reconfiguran las cuentas contables:
        Retención a una compra: move_type = out_invoice
        - La cuenta contable por conciliar es la cuenta contable por pagar del proveedor
        Retención a una venta: move_type = in_invoice
        - La cuenta contable por conciliar es la cuenta contable por cobrar del cliente
        
        Se divide la línea del contacto en por cada retención
        """
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
                for line in record.line_ids.filtered_domain([('l10n_pe_withhold_invoice_id', '!=', False)]):
                    if first_line:
                        update_line = {
                            'account_id': partner_account_id.id,
                            # 'display_type': 'payment_term',
                            'debit': line.credit,
                            'credit': line.debit,
                            'l10n_pe_withhold_invoice_id': line.l10n_pe_withhold_invoice_id.id,
                        }
                        first_line = False
                    else:
                        new_lines.append((0, 0, {
                            'name': line.name,
                            'account_id': partner_account_id.id,
                            'debit': line.credit,
                            'credit': line.debit,
                            'currency_id': line.currency_id.id,
                            'amount_currency': -1 * line.amount_currency,
                            'partner_id': line.partner_id.id,
                            'display_type': 'payment_term',
                            'l10n_pe_withhold_invoice_id': line.l10n_pe_withhold_invoice_id.id,
                        }))
                record.line_ids = [
                    (1, partner_line_id.id, update_line)] + new_lines