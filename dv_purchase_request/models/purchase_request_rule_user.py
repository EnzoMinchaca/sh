# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseRequestRuleUser(models.Model):
    _name = 'purchase.request.rule.user'

    rule_id = fields.Many2one('purchase.request.rule', string='Regla', required=True)
    user_id = fields.Many2one('res.users', string='Usuario', required=True)
    sequence = fields.Integer('Secuencia')

    @api.model
    def create(self, vals):
        # Obtener el valor de la secuencia máxima actual para la regla específica
        if 'rule_id' in vals:
            current_max_sequence = self.search([('rule_id', '=', vals['rule_id'])], order='sequence desc', limit=1).sequence
            vals['sequence'] = current_max_sequence + 1 if current_max_sequence else 1
        return super(PurchaseRequestRuleUser, self).create(vals)