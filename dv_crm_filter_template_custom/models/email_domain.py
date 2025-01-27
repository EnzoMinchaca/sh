from odoo import models,api, fields

class MailComposerInherit(models.TransientModel):
    _inherit = 'mail.compose.message'

    template_id = fields.Many2one(
        'mail.template', 'Use template',
        domain="[('type_lead', '=', type_pipeline_text_wizard),('model', '=', model), '|', ('user_id','=', False), ('user_id', '=', uid)]"
    )

    type_pipeline_text_wizard = fields.Char(
        string='Tipo de Pipeline',
        help='Este es un campo donde se obtendra tipo de pipeline del lead.'
    )

    def _compute_email_layout_xmlid(self):

        super(MailComposerInherit, self)._compute_email_layout_xmlid()

        for composer in self:
            if composer.model == 'crm.lead' and composer.res_ids:
                id_model = composer.res_ids
                lead_id = int(id_model.strip('[]'))
                lead = composer.env['crm.lead'].browse(lead_id)
                if lead.type_pipeline_text:
                    composer.type_pipeline_text_wizard = lead.type_pipeline_text.lower()
                else:
                    composer.type_pipeline_text_wizard = False
            else:
                composer.type_pipeline_text_wizard = False

        

        

        


        
        



        


    
        