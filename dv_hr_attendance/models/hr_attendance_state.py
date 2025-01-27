# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrAttendanceState(models.Model):
    _name = 'hr.attendance.state'

    name = fields.Char(string='Estado')
    color = fields.Char(string='Color')