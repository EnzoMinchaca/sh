# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    active_server_notification = fields.Boolean(string="Recibir notificaciones del servidor")

