# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError
import base64
import zipfile
from io import BytesIO

class Project(models.Model):
    _inherit = "project.project"

    sku = fields.Char(string='SKU')
    all_tasks_ready = fields.Boolean(string="All Tasks Ready", compute='_compute_all_tasks_ready')
    read_only_close = fields.Boolean(default=False)
    open = fields.Boolean(default=True)

    @api.depends('task_ids.stage_id')
    def _compute_all_tasks_ready(self):
        for project in self:
            project.all_tasks_ready = all(task.stage_id.is_closed  if 'is_closed' in task.stage_id else False  for task in project.task_ids)

    def action_close_project(self):
        self.ensure_one()
        if self.all_tasks_ready:
            self.write({'open': False})
            self.read_only_close = True
            for task in self.tasks:
                task.write({'open': False})
                task.read_only_close = True
            #Archivar el proyecto
            self.active = False


    def action_open_project(self):
        self.ensure_one()
        self.write({'open': True})
        self.read_only_close = False
        for task in self.tasks:
            task.write({'open': True})
            task.read_only_close = False
        
        
    #Relación de seguidores al crear
    @api.model
    def create(self, vals):
        record = super(Project, self).create(vals)
        if record.sale_order_id and record.sale_order_id.opportunity_id:
            #Busqueda del lead
            opportunity = record.sale_order_id.opportunity_id
            record.sku = opportunity.sku
            followers = opportunity.message_partner_ids.filtered(
                lambda p: p.id not in [opportunity.project_manager_id.partner_id.id]
            )
            #Cambio del nombre del proyecto
            name = opportunity.name
            record.name = name
            #Reasignación del nombre de la cuenta analítica
            analytic_account = record.analytic_account_id
            if analytic_account and opportunity.sku:
                analytic_account.name = opportunity.sku
            #Seguidores
            if followers:
                record.message_subscribe(partner_ids=followers.ids)
        return record
    
    #Descarga de archivos y categoría de proyectos
    def _read_group_categ_id(self, categories, domain, order):
        category_ids = self.env.context.get('default_categ_id')
        if not category_ids and self.env.context.get('group_expand'):
            category_ids = categories._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return categories.browse(category_ids)

    zip_file = fields.Binary(string='ZIP File')
    categ_id = fields.Many2one(
        'project.category', 'Categoría de proyecto', change_default=True, 
        group_expand='_read_group_categ_id')
    
    @api.onchange('sku')
    def _onchange_sku(self):
        for task in self.task_ids:
            task.sku = self.sku
    
    def action_download_attachments(self):
        self.ensure_one()  # Asegúrate de que se selecciona un solo proyecto
        attachment_ids = self.env['ir.attachment'].search([('res_model', '=', 'project.project'), ('res_id', '=', self.id)])
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for attachment in attachment_ids:
                file_data = base64.b64decode(attachment.datas)
                zip_file.writestr(attachment.name, file_data)
        
        zip_buffer.seek(0)
        zip_data = zip_buffer.read()
        zip_buffer.close()

        # Guardar el archivo zip en el campo temporal
        self.zip_file = base64.b64encode(zip_data).decode('utf-8')

        # Preparar el archivo zip para la descarga
        attachment_name = f"{self.name.replace(' ', '_')}_adjuntos.zip"
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=project.project&id=%d&field=zip_file&download=true&filename=%s' % (self.id, attachment_name),
            'target': 'self',
        }
    
    #Metodo para actualizar el SKU en los proyectos con leads
    def update_sku(self):
        for project in self:
            if project.sale_order_id and project.sale_order_id.opportunity_id:
                opportunity = project.sale_order_id.opportunity_id
                project.sku = opportunity.sku
        return True