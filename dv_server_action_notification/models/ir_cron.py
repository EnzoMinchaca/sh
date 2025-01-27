# -*- coding: utf-8 -*-

from odoo import models, fields, api


class IrCron(models.Model):
    _inherit = 'ir.cron'

    def write(self, vals):
        # Comprobamos si el campo 'active' ha cambiado en esta actualización
        if 'active' in vals:
            # Mensaje a enviar basado en el valor de 'active'
            message_init = (
                f"Se ha {'habilitado' if vals['active'] else 'deshabilitado'} "
                f"la acción del servidor ('{self.name}')"
            )
            # Buscamos a los usuarios que tienen la notificación activa
            users_to_notify = self.env['res.users'].search([('active_server_notification', '=', True)])

            if users_to_notify:
                # Enviamos el mensaje de notificación
                for user in users_to_notify:
                    message_user = (f"@{user.name}")
                    mention = f"<a href='#' data-oe-model='res.users' data-oe-id='{user.id}'>{message_user}</a>"
                    message_body = mention + " " + message_init
                    #Id de Odoo Bot
                    partner_root_id = self.env.ref('base.partner_root').id
                    #Se busca el canal entre el usuario y Odoo Bot
                    channel = self.env['discuss.channel'].search([
                        ('channel_partner_ids', 'in', [user.partner_id.id]),
                        ('channel_member_ids.partner_id', 'in', [user.partner_id.id, partner_root_id]),
                        ('channel_type', '=', 'chat'),
                    ])
                    channel = channel[0] if channel else None
                    #Si no existe el canal se crea
                    # if not channel:
                    #     channel = self.env['discuss.channel'].sudo().create({
                    #         'channel_partner_ids': [(4, user.partner_id.id)],
                    #         'channel_member_ids': [(0, 0, {'partner_id': user.partner_id.id}),
                    #                                (0, 0, {'partner_id': partner_root_id})],
                    #         'channel_type': 'chat',
                    #     })
                    alert_message = self.env['mail.message'].sudo().create({
                        'body': message_body,
                        'subject': 'Notificación de Acción del Servidor',
                        'message_type': 'comment',
                        'subtype_id': self.env.ref('mail.mt_comment').id,
                        'model': 'discuss.channel',
                        'res_id': channel.id if channel else False,
                        'author_id': self.env.ref('base.partner_root').id,  # Sistema (Odoo Bot)
                    })
                    #Se crea la notificación (mail.notification)
                    notification = self.env['mail.notification'].sudo().create({
                        'mail_message_id': alert_message.id,
                        'res_partner_id': user.partner_id.id,
                        'notification_type': 'inbox',
                    })
                    alert_message.sudo().write({
                        'notification_ids': [(4, notification.id)],
                        'notified_partner_ids': [(4, user.partner_id.id)],
                        'partner_ids': [(4, user.partner_id.id)],
                    })
        return super(IrCron, self).write(vals)