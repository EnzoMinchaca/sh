# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrShifts(models.Model):
    _name = 'hr.shifts'

    name = fields.Char(string='Turno')
    start_time = fields.Float(string='Hora de inicio')
    end_time = fields.Float(string='Hora de fin')