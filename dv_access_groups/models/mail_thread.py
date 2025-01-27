from odoo import models, fields, api

class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    show_send_message_button = fields.Boolean(compute='_compute_show_send_message_button')
    user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)
    
    @api.depends('user_id')
    def _compute_show_send_message_button(self):
        # ID del grupo que no debe ver el botón
        preventa_group_id = self.env.ref('dv_access_groups.group_crm_preventa').id
        
        for record in self:
        # Obtener los IDs de los grupos del usuario
            user_group_ids = record.env.user.groups_id.ids
        
        # Verificar si el usuario pertenece al grupo preestablecido
            record.show_send_message_button = preventa_group_id not in user_group_ids