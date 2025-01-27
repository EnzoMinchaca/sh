from odoo import models

class AccountPaymentRegisterInherit(models.TransientModel):
    _inherit = 'account.payment.register'
    
    def _reconcile_payments(self, to_process, edit_mode=False):

        domain = [
            ('parent_state', '=', 'posted'),
            ('account_type', 'in', self.env['account.payment']._get_valid_payment_account_types()),
            ('reconciled', '=', False),
        ]
        
        for vals in to_process:
            payment_lines = vals['payment'].line_ids.filtered_domain(domain)
            lines = vals['to_reconcile']
            
            # Ordenar las líneas por monto residual de mayor a menor
            lines = lines.filtered(lambda line: not line.l10n_pe_is_withholding_line)
            
            extra_context = {'forced_rate_from_register_payment': vals['rate']} if 'rate' in vals else {}

            for account in payment_lines.account_id:
                (payment_lines + lines)\
                    .with_context(**extra_context)\
                    .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)])\
                    .reconcile()
        
        super(AccountPaymentRegisterInherit, self)._reconcile_payments(to_process, edit_mode)
