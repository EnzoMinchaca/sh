# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from markupsafe import Markup
from odoo import api, fields, models, _
from odoo.tools.mail import is_html_empty


class CrmLeadNotPffered(models.TransientModel):
    _name = 'crm.lead.not.offered'
    _description = 'Get Not offered Reason'

    lead_ids = fields.Many2many('crm.lead', string='Leads')
    not_offered_reason_id = fields.Many2one('crm.not.offered.reason', 'Razón de no ofertado', required=True)
    not_offered_feedback = fields.Html(
        'Nota de no ofertado', sanitize=True
    )

    def action_not_offered_reason_apply(self):
        """Mark lead as Not Offered and apply the loss reason"""
        self.ensure_one()
        if not is_html_empty(self.not_offered_feedback):
            self.lead_ids._track_set_log_message(
                Markup('<div style="margin-bottom: 4px;"><p>%s:</p>%s<br /></div>') % (
                    _('Comentario de No ofertado'),
                    self.not_offered_feedback
                )
            )
        res = self.lead_ids.action_set_not_offered(not_offered_reason_id=self.not_offered_reason_id.id)
        return res
