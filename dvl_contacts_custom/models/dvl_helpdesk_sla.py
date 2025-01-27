from odoo import models, fields, api 

class HelpdeskSla(models.Model):
    _inherit = 'helpdesk.sla'

    tiempo_primera_respuesta = fields.Float(string='Tiempo de Primera Respuesta (horas)')


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    tiempo_primera_respuesta = fields.Float(string='Tiempo de Primera Respuesta (horas)', compute='_compute_tiempo_primera_respuesta', store=True)
    tiempo_primera_respuesta_esperado = fields.Float(store=True)
    
    tiempo_resolucion_esperado = fields.Float(string='Tiempo de Resolución Esperado (horas)')
    
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
    def create(self, vals):
        ticket = super(HelpdeskTicket, self).create(vals)
        ticket.action_timer_start()
        
        return ticket
    
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