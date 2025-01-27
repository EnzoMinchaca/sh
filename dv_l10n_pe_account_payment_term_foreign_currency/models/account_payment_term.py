from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta

class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    def _compute_terms(self, date_ref, currency, company, tax_amount, tax_amount_currency, sign, untaxed_amount, untaxed_amount_currency, cash_rounding=None):
        """Get the distribution of this payment term.
        :param date_ref: The move date to take into account
        :param currency: the move's currency
        :param company: the company issuing the move
        :param tax_amount: the signed tax amount for the move
        :param tax_amount_currency: the signed tax amount for the move in the move's currency
        :param untaxed_amount: the signed untaxed amount for the move
        :param untaxed_amount_currency: the signed untaxed amount for the move in the move's currency
        :param sign: the sign of the move
        :return (list<tuple<datetime.date,tuple<float,float>>>): the amount in the company's currency and
            the document's currency, respectively for each required payment date
        """
        if self.line_ids[0].l10n_pe_is_spot_term_line:
            self.ensure_one()
            company_currency = company.currency_id
            total_amount = tax_amount + untaxed_amount
            total_amount_currency = tax_amount_currency + untaxed_amount_currency

            pay_term = {
                'total_amount': total_amount,
                'discount_percentage': self.discount_percentage if self.early_discount else 0.0,
                'discount_date': date_ref + relativedelta(days=(self.discount_days or 0)) if self.early_discount else False,
                'discount_balance': 0,
                'line_ids': [],
            }

            if self.early_discount:
                # Early discount is only available on single line, 100% payment terms.
                discount_percentage = self.discount_percentage / 100.0
                if self.early_pay_discount_computation in ('excluded', 'mixed'):
                    pay_term['discount_balance'] = company_currency.round(total_amount - untaxed_amount * discount_percentage)
                    pay_term['discount_amount_currency'] = currency.round(total_amount_currency - untaxed_amount_currency * discount_percentage)
                else:
                    pay_term['discount_balance'] = company_currency.round(total_amount * (1 - discount_percentage))
                    pay_term['discount_amount_currency'] = currency.round(total_amount_currency * (1 - discount_percentage))

            rate = abs(total_amount_currency / total_amount) if total_amount else 0.0
            residual_amount = total_amount
            residual_amount_currency = total_amount_currency

            for i, line in enumerate(self.line_ids):
                term_vals = {
                    'date': line._get_due_date(date_ref),
                    'company_amount': 0,
                    'foreign_amount': 0,
                }

                if i == len(self.line_ids) - 1:
                    # The last line is always the balance, no matter the type
                    term_vals['company_amount'] = residual_amount
                    term_vals['foreign_amount'] = residual_amount_currency
                elif line.value == 'fixed':
                    # Fixed amounts
                    company_amount = sign * company_currency.round(line.value_amount / rate) if rate else 0.0
                    foreign_amount = sign * currency.round(line.value_amount)
                    term_vals['foreign_amount'] = foreign_amount
                    term_vals['company_amount'] = company_amount
                else:
                    # Percentage amounts
                    line_amount = company_currency.round(total_amount * (line.value_amount / 100.0))
                    line_amount_currency = currency.round(total_amount_currency * (line.value_amount / 100.0))
                    term_vals['company_amount'] = line_amount
                    term_vals['foreign_amount'] = line_amount_currency

                detractions_fields = ['l10n_pe_spot_amount', 'l10n_pe_spot_amount_currency']
                if line.l10n_pe_is_spot_term_line and all(hasattr(self.env['account.move'], field) for field in detractions_fields):
                    # Adaptación para que el módulo de detracciones sea un valor entero
                    term_vals['foreign_amount'] = line.invoice_id.l10n_pe_spot_amount
                    term_vals['company_amount'] = line.invoice_id.l10n_pe_spot_amount_currency
                retentions_fields = ['l10n_pe_withholding_amount', 'l10n_pe_withholding_amount_currency']
                if line.l10n_pe_is_withholding_term_line and all(hasattr(self.env['account.move'], field) for field in retentions_fields):
                    term_vals['foreign_amount'] = line.invoice_id.l10n_pe_withholding_amount
                    term_vals['company_amount'] = line.invoice_id.l10n_pe_withholding_amount_currency
                
                
                residual_amount -= term_vals['company_amount']
                residual_amount_currency -= term_vals['foreign_amount']
                pay_term['line_ids'].append(term_vals)

            return pay_term
        else:
            return super(AccountPaymentTerm, self)._compute_terms(date_ref, currency, company, tax_amount, tax_amount_currency, sign, untaxed_amount, untaxed_amount_currency, cash_rounding=cash_rounding)