# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, time, timedelta
from pytz import timezone
import pytz
import io
import xlsxwriter
import base64
from collections import defaultdict
from itertools import groupby

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    description = fields.Text(string='Descripción')    
    group_id = fields.Many2one('hr.group', string='Voulebard')
    equip_id = fields.Many2one('hr.equip', string='Equipo')
    shift_id = fields.Many2one('hr.shifts', string='Turno')
    state_id = fields.Many2one('hr.attendance.state', string='Estado')
    guardia_id = fields.Many2one('hr.department', related='employee_id.department_id', string='Guardia', store=True)
    vendor = fields.Char(related='employee_id.vendor', string='Vendor', store=True)
    break_in = fields.Datetime(string='Inicio de Refrigerio')
    break_out = fields.Datetime(string='Fin de Refrigerio')

    #Validación de asistencia
    @api.model
    def create(self, vals):
        res = super(HrAttendance, self).create(vals)
        if res.check_in:
            shifts = self.env['hr.shifts'].search([])
            if shifts:
                for shift in shifts:
                    local_check_in = res.check_in.astimezone(timezone('America/Lima'))
                    shift_start_time = datetime.combine(res.check_in.date(), time(hour=int(shift.start_time), minute=0)).astimezone(timezone('America/Lima'))
                    shift_end_time = datetime.combine(res.check_in.date(), time(hour=int(shift.end_time), minute=0)).astimezone(timezone('America/Lima'))
                    if shift_start_time < shift_end_time:  # Turno dentro del mismo día
                        if shift_start_time.time() <= local_check_in.time() < shift_end_time.time():
                            res.shift_id = shift.id
                    else:
                        if local_check_in.time() >= shift_start_time.time() or local_check_in.time() < shift_end_time.time():
                            res.shift_id = shift.id
            else:
                res.shift_id = False
            employee_id = res.employee_id.id
            self._check_consecutive_shifts(employee_id, res.shift_id.name, res.id, local_check_in)
            self._check_working_days(employee_id, res.id, local_check_in)
            res.state_id = self.env['hr.attendance.state'].search([('name', 'ilike', 'presente')], limit=1).id
        return res
    #Validación de 5 turnos consecutivos
    @api.model
    def _check_consecutive_shifts(self, employee_id, shift_name, id, local_check_in):
        consecutive_shifts = self.env['hr.attendance'].search([
            ('employee_id', '=', employee_id),
            ('id', '!=', id),
        ], order='check_in desc', limit=5)
        # consecutive_shift_names = [shift.shift_id.name for shift in consecutive_shifts]
        # if consecutive_shift_names.count(shift_name) >= 5:
        #     raise ValidationError("El empleado ya ha cumplido con los 5 turnos asignados para el %s." % (shift_name))
        if len(consecutive_shifts) >= 5:
            last_check_in = consecutive_shifts[0].check_in.astimezone(timezone('America/Lima'))
            if (local_check_in- last_check_in).days < 1:    #Se usa < 1 por defecto, indica la cantidad de dias de diferencia para que se reestablezca el ciclo
                raise ValidationError("El empleado ya ha cumplido con los 5 turnos asignados para el %s." % (shift_name))
    #Validación de 10 dias de descanso
    @api.model
    def _check_working_days(self, employee_id, id, local_check_in):
        last_attendances = self.env['hr.attendance'].search([
            ('employee_id', '=', employee_id),
            ('id', '!=', id),
            ('check_in', '!=', False),
        ], order='check_in desc', limit=10)
        if len(last_attendances) == 10:
            last_attendance_date = max(attendance.check_in.date() for attendance in last_attendances)
            next_working_day = last_attendance_date + timedelta(days=10)
            if local_check_in.date() <= next_working_day:
                raise ValidationError("El trabajador está en un período de descanso de 10 días y no puede marcar asistencia.")
    #Verificación de 1 registro por día
    @api.constrains('check_in')
    def _check_unique_day(self):
        for attendance in self:
            if attendance.check_in:
                check_in_date = attendance.check_in.date()
                attendance_exists = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_in', '>=', check_in_date),
                    ('check_in', '<', check_in_date + timedelta(days=1)),
                    ('id', '!=', attendance.id),
                ])
                if attendance_exists:
                    raise ValidationError("Ya no puede realizar más turnos, solo se puede registrar una asistencia en el día.")
    #Validación de horario de refrigerio, el refrigerio puede ser entre las 12:00 y 15:00
    @api.constrains('break_in', 'break_out')
    def _check_break_time(self):
        for attendance in self:
            if attendance.break_in:
                local_break_in = attendance.break_in.astimezone(timezone('America/Lima'))
                if 'día' in self.shift_id.name.lower():
                    if local_break_in.time() < time(hour=12, minute=0) or local_break_in.time() >= time(hour=15, minute=0):
                        raise ValidationError("El horario de refrigerio seleccionado no se encuentra dentro de los turnos disponibles.")
                if attendance.break_out:
                    local_break_out = attendance.break_out.astimezone(timezone('America/Lima'))
                    if local_break_in.time() >= local_break_out.time():
                        raise ValidationError("La hora de inicio de refrigerio debe ser menor a la hora de fin de refrigerio.")
    #Boton para inicio de refrigerio
    def action_start_break(self):
        for attendance in self:
            if not attendance.break_in:
                attendance.write({'break_in': fields.Datetime.now()})
    #Boton para fin de refrigerio
    def action_end_break(self):
        for attendance in self:
            if attendance.break_in and not attendance.break_out:
                attendance.write({'break_out': fields.Datetime.now()})
    #Reporte de excel
    def generate_excel(self):
        records = self.env['hr.attendance'].browse(self.env.context.get('active_ids', []))
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Control_Asistencia')

        # Establecer los formatos de la tabla
        header_style = workbook.add_format({
            'font_name': 'Aptos Narrow', 
            'font_size': 14, 
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#0066FF',
            'font_color': 'white',
        })
        data_style = workbook.add_format({
            'font_name': 'Aptos Narrow',
            'font_size': 11,
            'align': 'left',
            'valign': 'vcenter',
            'border': 7,
            'border_color': '#0066FF',
        })
        combined_cell_style = workbook.add_format({
            'font_name': 'Aptos Narrow',
            'bold': True,
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#002060',
            'font_color': 'white',
        })
        guardia_style = workbook.add_format({
            'font_name': 'Aptos Narrow',
            'font_size': 11,
            'bold': True,
            'bg_color': '#00B050',
            'font_color': 'black',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
        })
        # Datos de guardia y grupos
        guardias = set(record.employee_id.department_id.name for record in records if record.employee_id.department_id)
        grupos = set(record.group_id.name for record in records if record.group_id)
        worksheet.write('C2', 'GUARDIA', guardia_style)
        worksheet.write('D2', ', '.join(guardias), guardia_style)
        worksheet.write('E2', 'GRUPO', guardia_style)
        worksheet.write('F2', ', '.join(grupos), guardia_style)
        # Encabezados de tabla
        headers = [
            'N°',
            'VENDOR',
            'APELLIDOS Y NOMBRES',
            'EQUIPO',
            'ESTADO',
            'Observación/descripción'
        ]
        column_widths = [3, 10, 80, 17, 17, 30]
        for col, header in enumerate(headers):
            worksheet.write(2, col+1, header, header_style)
            worksheet.set_column(col+1, col+1, column_widths[col])
        # Escribir los datos de los registros seleccionados en el Excel
        state_colors = {state.name: state.color for state in self.env['hr.attendance.state'].search([])}
        for idx, record in enumerate(records, start=1):
            bg_color = state_colors.get(record.state_id.name, '') if record.state_id else ''
            state_style_with_bg = workbook.add_format({
                'font_name': 'Aptos Narrow',
                'font_size': 11,
                'align': 'center',
                'valign': 'vcenter',
                'border': 1,
                'border_color': '#0066FF',
                'bg_color': bg_color,
            })
            worksheet.write(idx+2, 1, idx, data_style)
            worksheet.write(idx+2, 2, record.employee_id.vendor if record.employee_id.vendor else '', data_style)
            worksheet.write(idx+2, 3, record.employee_id.name, data_style)
            worksheet.write(idx+2, 4, record.equip_id.name if record.equip_id else '', data_style)
            worksheet.write(idx+2, 5, record.state_id.name if record.state_id else '', state_style_with_bg)
            worksheet.write(idx+2, 6, record.description if record.description else '', data_style)
        # Suma de Estados del Personal
        worksheet.merge_range('I4:I5', 'TOTAL PERSONAL OPERACIONES MINA', combined_cell_style)
        worksheet.merge_range('J4:J5', len(records), combined_cell_style)
        worksheet.set_column(3, 8, 24)

        state_counts = defaultdict(int)
        for record in records:
            state_counts[record.state_id.name] += 1
        
        row = 5
        for state, count in state_counts.items():
            state_style = workbook.add_format({
                'font_name': 'Aptos Narrow',
                'font_size': 12,
                'bold': True,
                'border': 7,
                'bg_color': state_colors.get(state, ''),
            })
            worksheet.write(row, 8, state, state_style)
            worksheet.write(row, 9, count, state_style) 
            row += 1
        # Guardar el archivo Excel en memoria
        # worksheet.autofit()
        workbook.close()
        output.seek(0)
        excel_binary = base64.b64encode(output.read())
        # Crear un registro en el modelo donde almacenaremos el archivo Excel
        attachment = self.env['ir.attachment'].create({
            'name': 'Reporte de asistencia.xlsx',
            'type': 'binary',
            'datas': excel_binary,
            'res_model': self._name,
            'res_id': 0,
        })

        # Devolver una acción para descargar el archivo Excel recién creado
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }