from odoo import api, fields, models, _

class StageInherit(models.Model):
    _inherit = "crm.stage"
    @api.model
    def default_get(self, fields):     
        res=super(StageInherit, self).default_get(fields)
        if 'default_team_id' in self.env.context:
            team_id=self.env.context.get('default_team_id')
            res['team_id']=team_id
        return res