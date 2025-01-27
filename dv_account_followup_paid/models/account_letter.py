from odoo import models

class AccountLetter(models.Model):
    _inherit = 'account.letter'

    def action_open_business_doc(self):
        self.ensure_one()

        return {
            'name': 'Canje de letras',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_model': 'account.letter',
            'res_id': self.id,
            'target': 'current',
        }