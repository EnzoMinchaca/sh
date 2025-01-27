from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import float_compare, float_round
from odoo.tools.safe_eval import safe_eval

class TeamInherit(models.Model):
    _inherit = "crm.team"

    @api.model
    def action_your_pipeline_private(self):
        action = self.env["ir.actions.actions"]._for_xml_id("dv_crm_project_custom.crm_lead_action_pipeline_private")
        return self._action_update_to_pipeline_private(action)

    @api.model
    def action_your_pipeline_public(self):
        action = self.env["ir.actions.actions"]._for_xml_id("dv_crm_project_custom.crm_lead_action_pipeline_public")
        return self._action_update_to_pipeline_public(action)
    
    @api.model
    def _action_update_to_pipeline_private(self, action):
        user_team_id = self.env.ref('dv_crm_project_custom.team_pipeline_private').id
        if user_team_id:
            # To ensure that the team is readable in multi company
            user_team_id = self.search([('id', '=', user_team_id)], limit=1).id
        else:
            user_team_id = self.search([], limit=1).id
            action['help'] = "<p class='o_view_nocontent_smiling_face'>%s</p><p>" % _("Create an Opportunity")
            if user_team_id:
                if self.user_has_groups('sales_team.group_sale_manager'):
                    action['help'] += "<p>%s</p>" % _("""As you are a member of no Sales Team, you are showed the Pipeline of the <b>first team by default.</b>
                                        To work with the CRM, you should <a name="%d" type="action" tabindex="-1">join a team.</a>""",
                                        self.env.ref('sales_team.crm_team_action_config').id)
                else:
                    action['help'] += "<p>%s</p>" % _("""As you are a member of no Sales Team, you are showed the Pipeline of the <b>first team by default.</b>
                                        To work with the CRM, you should join a team.""")
        action_context = safe_eval(action['context'], {'uid': self.env.uid})
        if user_team_id:
            action_context['default_team_id'] = user_team_id
        # Modifica la condición del dominio para incluir el ID del equipo
        action_domain = safe_eval(action['domain'], {'team_id': user_team_id})
        action_domain.append(('team_id', '=', user_team_id))
        action['domain'] = action_domain
        action['context'] = action_context
        return action

    @api.model
    def _action_update_to_pipeline_public(self, action):
        user_team_id = self.env.ref('dv_crm_project_custom.team_pipeline_public').id
        if user_team_id:
            # To ensure that the team is readable in multi company
            user_team_id = self.search([('id', '=', user_team_id)], limit=1).id
        else:
            user_team_id = self.search([], limit=1).id
            action['help'] = "<p class='o_view_nocontent_smiling_face'>%s</p><p>" % _("Create an Opportunity")
            if user_team_id:
                if self.user_has_groups('sales_team.group_sale_manager'):
                    action['help'] += "<p>%s</p>" % _("""As you are a member of no Sales Team, you are showed the Pipeline of the <b>first team by default.</b>
                                        To work with the CRM, you should <a name="%d" type="action" tabindex="-1">join a team.</a>""",
                                        self.env.ref('sales_team.crm_team_action_config').id)
                else:
                    action['help'] += "<p>%s</p>" % _("""As you are a member of no Sales Team, you are showed the Pipeline of the <b>first team by default.</b>
                                        To work with the CRM, you should join a team.""")
        action_context = safe_eval(action['context'], {'uid': self.env.uid})
        if user_team_id:
            action_context['default_team_id'] = user_team_id
        # Modifica la condición del dominio para incluir el ID del equipo
        action_domain = safe_eval(action['domain'], {'team_id': user_team_id})
        action_domain.append(('team_id', '=', user_team_id))
        action['domain'] = action_domain

        action['context'] = action_context
        return action

    @api.model
    def _action_update_to_pipeline(self, action):
        user_team_id = self.env.user.sale_team_id.id
        if user_team_id:
            # Se asegura de que el equipo sea legible en multiempresa
            user_team_id = self.search([('id', '=', user_team_id)], limit=1).id
        else:
            user_team_id = self.search([], limit=1).id
            action['help'] = "<p class='o_view_nocontent_smiling_face'>%s</p><p>" % _("Create an Opportunity")
            if user_team_id:
                if self.user_has_groups('sales_team.group_sale_manager'):
                    action['help'] += "<p>%s</p>" % _("""As you are a member of no Sales Team, you are shown the Pipeline of the <b>first team by default.</b>
                                        To work with the CRM, you should <a name="%d" type="action" tabindex="-1">join a team.</a>""",
                                        self.env.ref('sales_team.crm_team_action_config').id)
                else:
                    action['help'] += "<p>%s</p>" % _("""As you are a member of no Sales Team, you are shown the Pipeline of the <b>first team by default.</b>
                                        To work with the CRM, you should join a team.""")

        # Ignorar IDs específicos si son los encontrados
        if user_team_id and (user_team_id == self.env.ref('dv_crm_project_custom.team_pipeline_private').id or 
                             user_team_id == self.env.ref('dv_crm_project_custom.team_pipeline_public').id):
            user_team_id = None

        action_context = safe_eval(action['context'], {'uid': self.env.uid})
        if user_team_id:
            action_context['default_team_id'] = user_team_id
         # Modifica la condición del dominio para incluir el ID del equipo
        action_domain = safe_eval(action['domain'], {'team_id': user_team_id})
        action_domain.append(('team_id', '=', user_team_id))
        action['domain'] = action_domain
        
        action['context'] = action_context
        return action