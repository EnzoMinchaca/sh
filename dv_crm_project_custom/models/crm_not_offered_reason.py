# -*- coding: utf-8 -*-

from odoo import fields, models, _


class NotOfferedReason(models.Model):
    _name = "crm.not.offered.reason"
    _description = 'Opp. Rason de No Ofertado'

    name = fields.Char('Description', required=True, translate=True)
    active = fields.Boolean('Active', default=True)
    leads_count = fields.Integer('Leads Count', compute='_compute_leads_count')

    def _compute_leads_count(self):
        lead_data = self.env['crm.lead'].with_context(active_test=False)._read_group(
            [('not_offered_reason_id', 'in', self.ids)],
            ['not_offered_reason_id'],
            ['__count'],
        )
        mapped_data = {not_offered_reason.id: count for not_offered_reason, count in lead_data}
        for reason in self:
            reason.leads_count = mapped_data.get(reason.id, 0)

    def action_not_offered_leads(self):
        return {
            'name': _('Leads'),
            'view_mode': 'tree,form',
            'domain': [('not_offered_reason_id', 'in', self.ids)],
            'res_model': 'crm.lead',
            'type': 'ir.actions.act_window',
            'context': {'create': False, 'active_test': False},
        }
