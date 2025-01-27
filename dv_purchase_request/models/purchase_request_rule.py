# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseRequestRule(models.Model):
    _name = 'purchase.request.rule'

    sequence = fields.Integer('Secuencia')
    rule_user_ids = fields.One2many('purchase.request.rule.user', 'rule_id', string='Usuarios')
    user_ids = fields.Many2many('res.users', string='Usuarios', compute='_compute_user_ids')
    rule = fields.Selection([
        ('<=', 'Menor o igual que'),
        ('<', 'Menor que'),
        ('=', 'Igual a'),
        ('>', 'Mayor que'),
        ('>=', 'Mayor o igual que'),
    ], 'Regla', required=True)
    company_id = fields.Many2one('res.company', 'Compañia', required=True, default=lambda self: self.env.company.id)
    currency_id = fields.Many2one('res.currency', 'Moneda', required=True, default=lambda self: self.env.company.currency_id.id)
    value = fields.Monetary('Valor', required=True, currency_field='currency_id')

    usd_currency_id = fields.Many2one('res.currency', 'Moneda USD', default=lambda self: self.env.ref('base.USD').id)
    value_usd = fields.Monetary('Valor en USD', currency_field='usd_currency_id')
    
    @api.depends('rule_user_ids')
    def _compute_user_ids(self):
        for rule in self:
            rule.user_ids = rule.rule_user_ids.mapped('user_id')
    
    #Aumentar el índice de la secuencia
    def create(self, vals):
        # Obtener el valor de la secuencia máxima actual
        current_max_sequence = self.search([], order='sequence desc', limit=1).sequence
        vals['sequence'] = current_max_sequence + 1 if current_max_sequence else 1
        return super(PurchaseRequestRule, self).create(vals)

    #Abrir vista de formulario
    def open_rule_form(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Usuarios responsables',
            'res_model': 'purchase.request.rule',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }