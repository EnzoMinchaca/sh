from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AccountLetterBank(models.TransientModel):
    _name = 'account.letter.bank'
    _description = 'Cuentas Bancarias de las letras'

    letter_id = fields.Many2one('account.letter', string='Letra', required=True)
    bank_id = fields.Many2one('res.bank', string='Banco', required=True)
    letter_line_ids = fields.Many2many('account.letter.line', string='Líneas de la letra', required=True)

    # Precarga las líneas de letras al crear el wizard
    @api.model
    def default_get(self, fields):
        res = super(AccountLetterBank, self).default_get(fields)
        letter_id = self.env.context.get('active_id')
        letter = self.env['account.letter'].browse(letter_id)
        res['letter_id'] = letter_id
        res['letter_line_ids'] = [(6, 0, letter.letter_line_ids.ids)]
        return res
    
    def action_confirm(self):
        for line in self.letter_id:
            line.write({
                'state': 'billing'
            })
        for line in self.letter_line_ids:
            line.write({
                'bank_id': self.bank_id.id,
            })
        return {'type': 'ir.actions.act_window_close'}