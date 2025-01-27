from odoo import models, fields, api, _
from datetime import datetime, timedelta

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    tiempo_primera_respuesta = fields.Float(string='Tiempo de Primera Respuesta (horas)', compute='_compute_tiempo_primera_respuesta', store=True)
    tiempo_primera_respuesta_esperado = fields.Float(store=True)
    
    tiempo_resolucion_esperado = fields.Float(string='Tiempo de Resolución Esperado (horas)')
    
    count_first_response_timer = fields.Float(string='Contador de primera respuesta', default=0.0)
    count_resolution_timer = fields.Float(string='Contador de tiempo de resolución', default=0.0)

    display_type = fields.Selection([('classic', 'Classic')], string="Display Type", default='classic')
    line_type_id = fields.Many2one('helpdesk.line.type', string="Type")
    ticket_origin = fields.Selection([
        ('web', 'Web'),
        ('email', 'Email'),
        ('manual', 'Manual'),
    ], string='Origen del ticket')

    #Campos con formato
    total_hours_spent_formatted = fields.Char(string='Horas totales invertidas (hh:mm)', compute='_compute_total_hours_spent_formatted', store=True)
    tiempo_primera_respuesta_formatted = fields.Char(string='Tiempo de Primera Respuesta (hh:mm)', compute='_compute_tiempo_primera_respuesta_formatted', store=True)
    
    @api.depends('total_hours_spent')
    def _compute_total_hours_spent_formatted(self):
        for ticket in self:
            total_hours = ticket.total_hours_spent or 0.0
            hours = int(total_hours)
            minutes = int((total_hours - hours) * 60)
            ticket.total_hours_spent_formatted = f"{hours:02}:{minutes:02}"
    
    @api.depends('tiempo_primera_respuesta')
    def _compute_tiempo_primera_respuesta_formatted(self):
        for ticket in self:
            tiempo_primera_respuesta = ticket.tiempo_primera_respuesta or 0.0
            hours = int(tiempo_primera_respuesta)
            minutes = int((tiempo_primera_respuesta - hours) * 60)
            ticket.tiempo_primera_respuesta_formatted = f"{hours:02}:{minutes:02}"

    @api.depends('create_date', 'message_ids')
    def _compute_tiempo_primera_respuesta(self):
        for ticket in self:
            first_response_message = ticket.message_ids.filtered(lambda m: m.message_type == 'comment').sorted('date')
            if first_response_message:
                first_response_date = first_response_message[0].date
                create_date = ticket.create_date
                # Calcular la diferencia en horas
                time_diff = first_response_date - create_date
                ticket.tiempo_primera_respuesta = time_diff.total_seconds() / 3600.0
                
                # Agregar un mensaje al ticket
                # ticket.message_post(body=f'El tiempo de primera respuesta fue de {ticket.tiempo_primera_respuesta:.2f} horas.')
            else:
                ticket.tiempo_primera_respuesta = 0.0
                
    @api.model_create_multi
    def create(self, list_value):
        for vals in list_value:
            if 'ticket_origin' not in vals:
                if self.env.context.get('default_ticket_origin') == 'manual':
                    vals['ticket_origin'] = self.env.context['default_ticket_origin']
                elif self.env.context.get('website_id'):
                    vals['ticket_origin'] = 'web'
                else:
                    vals['ticket_origin'] = 'email'

        tickets = super(HelpdeskTicket, self).create(list_value)

        for ticket in tickets:
            # if not ticket.display_timesheet_timer:
            #     ticket.display_timesheet_timer = True
            ticket.action_timer_start()

        return tickets
    
    def _sla_apply(self, keep_reached=False):
        sla_statuses = super(HelpdeskTicket, self)._sla_apply(keep_reached=keep_reached)

        for ticket in self:
            if ticket.sla_ids:
                print(" _sla_apply SLA IDs: ", ticket.sla_ids)
                ticket.tiempo_primera_respuesta_esperado = min(ticket.sla_ids.mapped('tiempo_primera_respuesta'))
                ticket.tiempo_resolucion_esperado = max(ticket.sla_ids.mapped('time'))
            else:
                ticket.tiempo_primera_respuesta_esperado = 0.0
                ticket.tiempo_resolucion_esperado = 0.0

        return sla_statuses
    
    def action_count_timer(self):
        open_tickets = self.env['helpdesk.ticket'].search([('stage_id.fold', '=', False)])
        now = fields.Datetime.now()
        for record in open_tickets:
            now = fields.Datetime.now()
            if record.tiempo_primera_respuesta == 0.0:
                # Calcular la diferencia entre la fecha actual y la fecha de creación en horas decimales
                time_diff = now - record.create_date
                record.count_first_response_timer = round(time_diff.total_seconds() / 3600.0, 2)
            
            if record.is_timer_running:
                # Calcular la diferencia entre la fecha actual y la fecha de creación en horas decimales
                time_diff = now - record.create_date
                record.count_resolution_timer = round(time_diff.total_seconds() / 3600.0, 2)
    
    # @api.onchange('user_id')
    # def _onchange_user_id(self):
    #     timer = self.user_timer_id
    #     print("timer: ", timer)
    
    def write(self, values):
        res = False
        for record in self:
            if 'user_id' in values:
                old_user_id = record.user_id.id
                old_user_timer = record.user_timer_id
                res = super(HelpdeskTicket, record).write(values)
                new_user_timer = self.env['timer.timer'].search(
                    [
                        ('res_id', '=', record.id), 
                        ('res_model', '=', 'helpdesk.ticket'),
                        ('user_id', '=', record.user_id.id)
                    ], limit=1)
                if new_user_timer:
                    new_user_timer.sudo().unlink()
                if old_user_timer:
                    old_user_timer.user_id = record.user_id.id
        return super(HelpdeskTicket, self).write(values)
    
    def action_direct_timer_stop(self):
        if self.user_timer_id.timer_start and self.display_timesheet_timer:
            minutes_spent = self.user_timer_id._get_minutes_spent()
            minimum_duration = int(self.env['ir.config_parameter'].sudo().get_param('timesheet_grid.timesheet_min_duration', 0))
            rounding = int(self.env['ir.config_parameter'].sudo().get_param('timesheet_grid.timesheet_rounding', 0))
            minutes_spent = self._timer_rounding(minutes_spent, minimum_duration, rounding)
            values = {
                'project_id': self.project_id.id,
                'date': fields.Datetime.now(),
                'name': self.description,
                'user_id': self.user_id.id,
                'unit_amount': minutes_spent * 60 / 3600,
            }
            timesheet = self.env['account.analytic.line'].create(values)
            self.write({
                'timer_start': False,
                'timer_pause': False
            })
            self.timesheet_ids = [(4, timesheet.id, None)]
            self.user_timer_id.unlink()

        return False