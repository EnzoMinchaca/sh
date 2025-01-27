# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ServerActions(models.Model):
    _name = 'ir.actions.server'
    _inherit = ['ir.actions.server']

    state = fields.Selection(selection_add=[
        ('whatsapp', 'Enviar Whatsapp'),
    ], ondelete={'whatsapp': 'cascade'})

    whatsapp_template_id = fields.Many2one(
        'whatsapp.template', 'Plantilla de Whatsapp',
        compute='_compute_whatsapp_template_id',
        ondelete='set null', readonly=False, store=True,
        domain="[('model_id', '=', model_id), ('status', '=', 'approved')]",
    )

    whatsapp_method = fields.Selection(
        selection=[('whatsapp', 'Whatsapp (sin nota)'), ('comment', 'Whatsapp (con nota)'), ('note', 'Nota solamente')],
        string='Enviar Whatsapp Como',
        compute='_compute_whatsapp_method',
        readonly=False, store=True)
    
    @api.depends('state')
    def _compute_available_model_ids(self):
        mail_thread_based = self.filtered(lambda action: action.state == 'whatsapp')
        if mail_thread_based:
            mail_models = self.env['ir.model'].search([('is_mail_thread', '=', True), ('transient', '=', False)])
            for action in mail_thread_based:
                action.available_model_ids = mail_models.ids
        super(ServerActions, self - mail_thread_based)._compute_available_model_ids()

    @api.depends('model_id', 'state')
    def _compute_whatsapp_template_id(self):
        to_reset = self.filtered(
            lambda act: act.state != 'whatsapp' or \
                        (act.model_id != act.whatsapp_template_id.model_id)
        )
        if to_reset:
            to_reset.whatsapp_template_id = False
    
    @api.depends('state')
    def _compute_whatsapp_method(self):
        to_reset = self.filtered(lambda act: act.state != 'whatsapp')
        if to_reset:
            to_reset.whatsapp_method = False
        other = self - to_reset
        if other:
            other.whatsapp_method = 'whatsapp'
    
    @api.constrains('state', 'model_id')
    def _check_whatsapp_model_coherency(self):
        for action in self:
            if action.state == 'whatsapp' and (action.model_id.transient or not action.model_id.is_mail_thread):
                raise ValidationError(_("El envío de Whatsapp sólo puede realizarse en un mail.thread o en un modelo transitorio"))
    
    @api.constrains('model_id', 'template_id')
    def _check_whatsapp_model_template_coherency(self):
        for action in self.filtered(lambda act: act.state == 'whatsapp'):
            if action.whatsapp_template_id and action.whatsapp_template_id.model_id != action.model_id:
                raise ValidationError(
                    _('La plantilla de Whatsapp del %(action_name)s no coincide con el modelo de acción.',
                      action_name=action.name
                     )
                )

    def _run_action_whatsapp_multi(self, eval_context=None):
        if not self.whatsapp_template_id or self._is_recompute():
            return False
        
        records = eval_context.get('records') or eval_context.get('record')
        if not records:
            return False
        
        composer = self.env['whatsapp.composer'].with_context(
            default_res_model=records._name,
            default_res_ids=records.ids,
            default_wa_template_id=self.whatsapp_template_id.id,
        ).create({})
        composer.action_send_whatsapp_template()
        return False

    @api.depends('state', 'update_field_id', 'crud_model_id', 'value', 'evaluation_type', 'template_id', 'partner_ids', 'activity_summary', 'sms_template_id', 'webhook_url', 'whatsapp_template_id')
    def _compute_name(self):
        super(ServerActions, self)._compute_name()
        
        to_update = self.filtered(lambda action: action.state == 'whatsapp' and action.base_automation_id)
        for action in to_update:
            action.name = _(
                'Enviar WhatsApp: %(template_name)s',
                template_name=action.whatsapp_template_id.name
            )