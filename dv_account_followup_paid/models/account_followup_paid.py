from odoo import fields, models, api

class AccountFollowupPaid(models.Model):
    _name = 'account.followup.paid'
    _description = 'Seguimiento de Cuentas Pagadas'

    date = fields.Date(string="Fecha de Emisión")
    document_number = fields.Char(string="N° de Documento")
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Cliente'
    )
    account_payment_date = fields.Date(
        string="Fecha de Pago",
    )
    seller_account = fields.Many2one(
        comodel_name='res.users',
        string="Vendedor",
    )
    amount_no_sign_pen = fields.Monetary(
        string='Amount (Positive)',
        compute='_compute_amount_no_sign',
        store=True,
        currency_field='currency_pen_id'
    )
    amount_no_sign_usd = fields.Monetary(
        string='Amount (Positive)',
        compute='_compute_amount_no_sign',
        store=True,
        currency_field='currency_usd_id'
    )
    
    currency_usd_id = fields.Many2one('res.currency', string='Currency USD', default=lambda self: self.env.ref('base.USD').id)
    currency_pen_id = fields.Many2one('res.currency', string='Currency PEN', default=lambda self: self.env.ref('base.PEN').id)

    account_move_line_id = fields.Many2one(
        comodel_name='account.move.line',
        string='Factura'
    )

    related_move_id = fields.Many2one(
        'account.move', 
        string='Factura Relacionada'
    )

    account_letter_id = fields.Many2one(
        'account.letter', 
        string='Canje de Letra Relacionado'
    )

    year = fields.Integer()

    month = fields.Integer()






