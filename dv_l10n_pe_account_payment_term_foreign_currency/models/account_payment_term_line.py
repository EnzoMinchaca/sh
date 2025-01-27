from odoo import api, fields, models, _

class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"
    
    l10n_pe_is_spot_term_line = fields.Boolean(string='Es cuota de detracción', default=False)
    l10n_pe_is_withholding_term_line = fields.Boolean(string='Es cuota de retención', default=False)
    invoice_id = fields.Many2one('account.move', string='Factura')