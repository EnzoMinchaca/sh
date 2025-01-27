# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    groups = fields.Many2many(
        'res.groups', 
        string="Groups with Read Access", 
        compute='_compute_groups_with_access'
    )

    @api.depends('user_id')
    def _compute_groups_with_access(self):
        for lead in self.sudo():
            if lead.user_id:
                groups_with_read_access = self.env['res.groups'].sudo().search([
                    ('model_access', '!=', False),
                    ('model_access.model_id', '=', self.env.ref('crm.model_crm_lead').id),
                    ('model_access.perm_read', '=', True),
                    ('users', 'in', [self.env.user.id])
                ])
                if groups_with_read_access:
                    lead.groups = groups_with_read_access
                else:
                    lead.groups = False
            else:
                lead.groups = False

    def _message_post_after_hook(self, message, msg_vals):
        restricted_groups = [
            # 'dv_access_groups.group_crm_preventa',
            'dv_access_groups.group_crm_operaciones',
        ]

        # Verifica si es un mensaje (y no una nota)
        if message.subtype_id.internal == False and message.message_type != 'notification':
            # Verifica si el usuario pertenece a alguno de los grupos restringidos
            if any(self.env.user.has_group(group) for group in restricted_groups):
                raise AccessError("No tiene permisos para enviar mensajes, por favor contacte al administrador.")

        if self.email_from and not self.partner_id:
            # we consider that posting a message with a specified recipient (not a follower, a specific one)
            # on a document without customer means that it was created through the chatter using
            # suggested recipients. This heuristic allows to avoid ugly hacks in JS.
            new_partner = message.partner_ids.filtered(
                lambda partner: partner.email == self.email_from or (self.email_normalized and partner.email_normalized == self.email_normalized)
            )
            if new_partner:
                if new_partner[0].email_normalized:
                    email_domain = ('email_normalized', '=', new_partner[0].email_normalized)
                else:
                    email_domain = ('email_from', '=', new_partner[0].email)
                self.search([
                    ('partner_id', '=', False), email_domain, ('stage_id.fold', '=', False)
                ]).write({'partner_id': new_partner[0].id})
        return super(CrmLead, self)._message_post_after_hook(message, msg_vals)