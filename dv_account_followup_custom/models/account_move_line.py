
from odoo import fields, models, api
import logging
_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    new_move_name = fields.Char(compute='_compute_new_move_name')

    amount_usd = fields.Monetary(
        string='Importe en $',
        currency_field='currency_id',
        compute="_compute_amount_usd_pen",
        store=True, readonly=False
    )
    currency_usd_id = fields.Many2one('res.currency', string='Currency USD', default=lambda self: self.env.ref('base.USD').id)

    amount_pen = fields.Monetary(
        string='Importe en S/',
        currency_field='currency_id',
        compute="_compute_amount_usd_pen",
        store=True, readonly=False
    )
    currency_pen_id = fields.Many2one('res.currency', string='Currency PEN', default=lambda self: self.env.ref('base.PEN').id)

    new_date = fields.Date(compute='_compute_new_date', store=True)

    edi_state = fields.Char(compute="_compute_edi_state", store=True)

    @api.depends('currency_id','currency_id.name', 'amount_residual', 'new_move_name', 'move_id.letter_id', 'move_id.letter_id.letter_line_ids')
    def _compute_amount_usd_pen(self):
        for move_line in self:
            if move_line.journal_id.name == "Letras por cobrar" and move_line.move_id.letter_id and move_line.move_id.letter_id.letter_line_ids:
                for letter in move_line.move_id.letter_id.letter_line_ids:
                    if letter.nro_letter == move_line.new_move_name:
                        if move_line.move_id.letter_id.currency_id.name == 'PEN':
                            move_line.amount_pen = letter.amount_total

                        elif move_line.move_id.letter_id.currency_id.name == 'USD':
                            move_line.amount_usd = letter.amount_total
            else:
                if move_line.currency_id.name == 'PEN':
                    move_line.amount_pen = move_line.amount_residual_currency

                elif move_line.currency_id.name == 'USD':
                    move_line.amount_usd = move_line.amount_residual_currency

    @api.depends('move_name', 'journal_id', 'name')
    def _compute_new_move_name(self):
        for move_line in self:
            if move_line.journal_id.name == "Letras por cobrar":
                move_line.new_move_name = move_line.name
            else: 
                move_line.new_move_name = move_line.move_name
    
    @api.depends('invoice_date', 'journal_id')
    def _compute_new_date(self):
        for move_line in self:
            if move_line.journal_id.name == "Letras por cobrar":
                move_line.new_date = move_line.date
            else: 
                move_line.new_date = move_line.invoice_date

    @api.depends('journal_id.name', 'move_id.edi_state')
    def _compute_edi_state(self):
        for move_line in self:
            if move_line.journal_id.name == "Letras por cobrar":
                move_line.edi_state = "sent"
            else: 
                move_line.edi_state = move_line.move_id.edi_state