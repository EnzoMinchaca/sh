from odoo import models, fields, api

class CrmLeadInherit(models.Model):
    _inherit = 'crm.lead'

    type_pipeline_text = fields.Char(string='Tipo de pipeline',compute='_compute_calculate_team',store=True)

    @api.depends('team_id')
    def _compute_calculate_team(self):
        for record in self:
            if record.team_id and record.team_id.name == 'Public Pipeline Team':
                record.type_pipeline_text = 'gobierno'
            elif record.team_id and record.team_id.name == 'Private Pipeline Team':
                record.type_pipeline_text = 'privadas'
            else:
                record.type_pipeline_text = False

