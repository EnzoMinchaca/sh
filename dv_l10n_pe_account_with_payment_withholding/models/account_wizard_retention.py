from odoo import models, api, fields

class AccountWizardRetention(models.Model):
    _name = 'account.wizard.retention'

    total_amount_static = fields.Float(store=True)
    # Aquí añades el campo currency_id relacionado con res.currency
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    state_chang_date = fields.Boolean(default=False)
    
    # Aquí asociamos el campo 'Monetary' con el campo currency_id
    l10n_pe_withholding_amount_currency = fields.Monetary(
        help='Monto de retención en moneda de la empresa',
        store=True,
        currency_field='currency_id'
    )
    
    payment_difference_custom = fields.Monetary(
        help='Monto de diferencia',
        store=True,
        currency_field='currency_id'
    )