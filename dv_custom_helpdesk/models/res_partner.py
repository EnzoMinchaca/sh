from odoo import models, fields, api

class Partner(models.Model):
    _inherit = 'res.partner'

    ticket_ids = fields.One2many('helpdesk.ticket', 'partner_id', string='Tickets')
    ticket_count = fields.Integer("Cantidad Tickets", compute='_compute_ticket_count', store=True)
    count_tickets = fields.Integer(string="Cantidad de Tickets", compute='_compute_count_tickets', store=True)

    @api.depends('ticket_ids', 'ticket_ids.partner_id')
    def _compute_count_tickets(self):
        
        for partner in self:
            tickets = self.env['helpdesk.ticket'].search([('partner_id', '=', partner.id)])
            partner.count_tickets = len(tickets)
            partner.ticket_count = len(tickets)