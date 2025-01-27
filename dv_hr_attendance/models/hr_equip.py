# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrEquip(models.Model):
    _name = 'hr.equip'

    name = fields.Char(string='Equipo')