# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, get_lang
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sku = fields.Many2one('account.analytic.account', 'SKU')
    rule_user_ids = fields.Many2many('purchase.request.rule.user', string='Usuarios responsables')
    rule_id = fields.Many2one('purchase.request.rule', string='Regla aplicada')
    purchase_request_id = fields.Many2one('purchase.request', string='Solicitud de compra')
    state = fields.Selection(selection_add=[
        ('purchase_draft', 'Borrador de Orden'),
    ])
    is_purchase_confirmed = fields.Boolean('Orden de compra confirmada', default=False)

    def identify_applicable_rule(self):
        # Obtener todas las reglas ordenadas por valor ascendente
        rules = self.env['purchase.request.rule'].search([], order='value asc')
        applicable_rule = None
        
        for rule in rules:
            if self.currency_id == self.env.ref('base.USD'):
                value_compare = rule.value_usd
            else:
                value_compare = rule.value
            
            # Verificar cuál regla cumple con el monto total de la orden de compra
            if rule.rule == '<=' and self.amount_total <= value_compare:
                applicable_rule = rule
            elif rule.rule == '<' and self.amount_total < value_compare:
                applicable_rule = rule
            elif rule.rule == '=' and self.amount_total == value_compare:
                applicable_rule = rule
            elif rule.rule == '>' and self.amount_total > value_compare:
                applicable_rule = rule
            elif rule.rule == '>=' and self.amount_total >= value_compare:
                applicable_rule = rule

            # Rompemos el bucle cuando encontramos la primera regla aplicable
            if applicable_rule:
                break
        
        if applicable_rule:
            self.rule_id = applicable_rule
        else:
            raise UserError('Es necesario definir una regla para confirmar la orden de compra')
        
    def validate_and_assign_users(self):
        if not self.rule_id:
            raise UserError('No se ha identificado una regla. Por favor, ejecuta primero la identificación de la regla.')
        
        applicable_rule_users = self.rule_id.rule_user_ids.mapped('user_id')
        if self.env.user not in applicable_rule_users:
            raise UserError('No tienes permisos para confirmar la orden de compra')

        # Asignar el usuario actual en el campo rule_user_ids si es parte de los responsables
        for role_user in self.rule_id.rule_user_ids:
            if role_user.user_id == self.env.user:
                self.rule_user_ids = [(4, role_user.id)]
                break

        # Verificar si todos los usuarios de la regla están en la orden de compra
        self.check_all_rule_users()

    def check_all_rule_users(self):
        # Obtener los usuarios responsables definidos en la orden de compra (campo rule_user_ids)
        order_user_ids = self.rule_user_ids.mapped('user_id')
        if self.rule_id:
            applicable_rule_users = self.rule_id.rule_user_ids.mapped('user_id')
            
            # Verificar si todos los usuarios de la regla están en rule_user_ids.user_id
            if order_user_ids == applicable_rule_users:
                self.is_purchase_confirmed = True

        return False
    
    # Botone de enviar orden
    def button_send_draft_order(self):
        self.identify_applicable_rule()
        if self.rule_id:
            self.create_pending_activities()
            self.write({'state': 'purchase_draft'})
    
    def create_pending_activities(self):
        for user in self.rule_id.rule_user_ids.mapped('user_id'):
            # Crear una actividad para cada usuario
            self.env['mail.activity'].create({
                'res_model_id': self.env.ref('purchase.model_purchase_order').id,  # Modelo 'purchase.order'
                'res_id': self.id,  # El ID de la orden de compra actual
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,  # Tipo de actividad: Pendiente
                'summary': 'Orden por Aprobar %s' % self.name,  # Título de la actividad
                'user_id': user.id,  # Usuario asignado para la actividad
                'date_deadline': fields.Date.today(),  # Fecha límite (puedes ajustarla si es necesario)
            })
    
    def button_confirm(self):
        if self.state == 'purchase_draft':
            self.write({'state': 'sent'})
        res = super(PurchaseOrder, self).button_confirm()
        return res
        
        