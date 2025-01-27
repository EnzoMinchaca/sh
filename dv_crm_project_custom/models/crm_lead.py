from odoo import api, fields, models
from datetime import timedelta

class Lead(models.Model):
    _inherit = "crm.lead"
    
    #Relación de seguidores
    project_manager_id = fields.Many2one(
        'res.users', string='Gerente de proyecto',
        domain="[('share', '=', False)]",
        check_company=True, index=True)
    expected_revenue = fields.Monetary('Ingreso esperado', currency_field='company_currency', tracking=False)
    sku = fields.Char(string='SKU')
    tipo_requerimiento = fields.Selection(string = 'Tipo de requerimiento', selection=[('CORREO ELECTRONICO', 'CORREO ELECTRÓNICO'), ('SEACE', 'SEACE')] , store = True)
    create_date_custom = fields.Datetime(default=lambda self: fields.Datetime.now(), string="Fecha de creación:")
    # Datos de la pestaña de contacto del cliente
    contact_line_id = fields.Many2one('contact.line', string='Nombres y Apellidos', domain="[('partner_id', '=', partner_id)]", store=True)
    contact_area = fields.Char(string='Área', readonly=True, store=True)
    contact_funcion = fields.Char(string='Función', readonly=True, store=True)
    contact_email = fields.Char(string='Email', readonly=True, store=True)
    contact_mobile = fields.Char(string='Celular', readonly=True, store=True)
    # Campo de espera
    field_wait = fields.Boolean(string='En espera', default=False)
    stage_name = fields.Char(related='stage_id.name', string='Nombre de etapa', store=True)
    
    def action_mark_as_in_wait(self):
        self.write({'active':False, 'field_wait':True, 'probability':0})

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            pass
            #self._select_first_contact()
        else:
            self.contact_line_id = False
            self.contact_email = False
            self.contact_mobile = False
            self.contact_area = False
            self.contact_funcion = False
    
    @api.onchange('contact_line_id')
    def _onchange_contact_line_id(self):
        if self.contact_line_id:
            self.contact_email = self.contact_line_id.email
            self.contact_mobile = self.contact_line_id.mobile
            self.contact_area = self.contact_line_id.area
            self.contact_funcion = self.contact_line_id.funcion
        else:
            self.contact_email = False
            self.contact_mobile = False
            self.contact_area = False
            self.contact_funcion = False
    
    def _select_first_contact(self):
        if self.partner_id:
            first_contact_line = self.env['contact.line'].search([('partner_id', '=', self.partner_id.id)], limit=1)
            if first_contact_line:
                self.contact_line_id = first_contact_line
                self.contact_email = first_contact_line.email
                self.contact_mobile = first_contact_line.mobile
                self.contact_area = first_contact_line.area
                self.contact_funcion = first_contact_line.funcion
            else:
                self.contact_line_id = False
                self.contact_email = False
                self.contact_mobile = False
                self.contact_area = False
                self.contact_funcion = False
    @api.model
    def create(self, vals):
        record = super(Lead, self).create(vals)
        # if record.partner_id:
        #     record._select_first_contact()
        if 'project_manager_id' in vals and record.project_manager_id.partner_id:
            record.message_subscribe(partner_ids=[record.project_manager_id.partner_id.id])
        return record

    def write(self, vals):
        res = False  # Inicializar la variable res
        if 'contact_line_id' in vals and vals['contact_line_id']:
            contact_line = self.env['contact.line'].browse(vals['contact_line_id'])
            # Copiamos los valores de contacto al guardar
            vals.update({
                'contact_email': contact_line.email,
                'contact_mobile': contact_line.mobile,
                'contact_area': contact_line.area,
                'contact_funcion': contact_line.funcion,
            })
        for record in self:
            # Relación de seguidores
            old_project_manager_partner_id = record.project_manager_id.partner_id.id if record.project_manager_id else None
            res = super(Lead, record).write(vals)
            new_project_manager_partner_id = record.project_manager_id.partner_id.id if record.project_manager_id else None
            # Si cambia el gerente de proyecto
            if 'project_manager_id' in vals and old_project_manager_partner_id and old_project_manager_partner_id != new_project_manager_partner_id:
                record.message_unsubscribe(partner_ids=[old_project_manager_partner_id])
            if 'project_manager_id' in vals and new_project_manager_partner_id:
                record.message_subscribe(partner_ids=[new_project_manager_partner_id])
            # Reinicio de color
            # if vals.get('stage_id'):
            #     record.color = 0
        return res
    
    @api.model
    def _prepare_opportunity_quotation_context(self):
        quotation_context = super(Lead, self)._prepare_opportunity_quotation_context()
        if self.sku:
            plan_analitico = self.env['account.analytic.plan'].search([('name', '=', 'Proyectos')], limit=1)
            #Buscar la cuenta analítica
            analytic_exist = self.env['account.analytic.account'].search([('name', '=', self.sku)], limit=1)
            if analytic_exist:
                analytic_account = analytic_exist
            else:
                analytic_account = self.env['account.analytic.account'].create({
                    'name': self.sku,
                    'plan_id': plan_analitico.id,
                })
            # Agregar la cuenta analítica al contexto para la creación de la cotización
            quotation_context['default_analytic_account_id'] = analytic_account.id
        return quotation_context
    
    #Motivos no ofertados
    not_offered_reason_id = fields.Many2one(
        'crm.not.offered.reason', string='Razón de no ofertado',
        index=True, ondelete='restrict', tracking=True)

    def action_set_not_offered(self, **additional_values):
        res = self.action_archive()
        if additional_values:
            self.write(dict(additional_values))
        return res

    def toggle_active(self):
        res = super(Lead, self).toggle_active()
        activated = self.filtered(lambda lead: lead.active)
        archived = self.filtered(lambda lead: not lead.active)
        if activated:
            for lead in activated:
                if lead.lost_reason_id:
                    lead.write({'lost_reason_id': False})
                elif lead.not_offered_reason_id:
                    lead.write({'not_offered_reason_id': False})
            activated._compute_probabilities()
        if archived:
            archived.write({'probability': 0, 'automated_probability': 0})
        if self.field_wait == True:
            self.write({'active':True, 'field_wait':False})
        return res
    
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'stage_id' in init_values and self.probability == 100 and self.stage_id:
            return self.env.ref('crm.mt_lead_won')
        elif 'lost_reason_id' in init_values and self.lost_reason_id:
            return self.env.ref('crm.mt_lead_lost')
        elif 'not_offered_reason_id' in init_values and self.not_offered_reason_id:
            return self.env.ref('dv_crm_project_custom.mt_lead_not_offered')
        elif 'stage_id' in init_values:
            return self.env.ref('crm.mt_lead_stage')
        elif 'active' in init_values and self.active:
            return self.env.ref('crm.mt_lead_restored')
        elif 'active' in init_values and not self.active:
            return self.env.ref('crm.mt_lead_lost')
        return super(Lead, self)._track_subtype(init_values)