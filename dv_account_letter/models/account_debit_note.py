# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError


class AccountDebitNote(models.TransientModel):
    _inherit = 'account.debit.note'

    def create_debit(self):
        self.ensure_one()
        new_moves = self.env['account.move'].sudo()
        for move in self.move_ids.sudo().with_context(include_business_fields=True): #copy sale/purchase links
            default_values = self._prepare_default_values(move)
            new_move = move.sudo().copy(default=default_values)
            move_msg = _("Esta nota de débito fue creada desde: %s", move._get_html_link())
            new_move.message_post(body=move_msg)
            new_moves |= new_move

        action = {
            'name': _('Notas de Débito'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'context': {'default_move_type': default_values['move_type']},
        }
        if len(new_moves) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': new_moves.id,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', new_moves.ids)],
            })
        return action