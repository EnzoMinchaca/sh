# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrGroup(models.Model):
    _name = 'hr.group'

    name = fields.Char(string='Nombre')