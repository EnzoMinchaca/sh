# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.http import request
from odoo.tools import float_round
import datetime
from odoo.addons.hr_attendance.controllers.main import HrAttendance

class HrAttendanceController(HrAttendance):

    @http.route(["/hr_attendance/<token>"], type='http', auth='public', website=True, sitemap=True)
    def open_kiosk_mode(self, token):
        response = super().open_kiosk_mode(token)
        if response.status_code == 200:  # Verificar si la respuesta es exitosa
            # Modificar la respuesta según tus necesidades
            # Agregar el campo 'vendor' a cada empleado en 'employee_list'
            data = response.qcontext.get('kiosk_backend_info')
            if data and 'employees' in data:
                for employee in data['employees']:
                    # Supongamos que 'vendor' es un campo adicional en el modelo 'hr.employee'
                    # y deseamos agregarlo a cada empleado en la lista
                    # Aquí obtendrías el valor de 'vendor' para cada empleado y lo agregarías al diccionario
                    employee_record = request.env['hr.employee'].sudo().browse(employee['id'])
                    employee['vendor'] = employee_record.vendor  # Asignar el valor del campo 'vendor'
        return response