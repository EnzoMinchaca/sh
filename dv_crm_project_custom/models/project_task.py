from odoo import fields, models, api
from odoo.exceptions import AccessError, ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)

class Task(models.Model):
    _inherit = "project.task"

    alert_hour = fields.Float(string="Hora para la Alerta", default=9.5)
    alert_users = fields.Many2many(comodel_name='res.users', string="Usuarios Notificados", compute="_compute_alert_users", store=True, readonly=False)
    generate_task = fields.Boolean(default=False)
    days_alert = fields.Integer(string="Cantidad de Días", default=3)
    sku = fields.Char(string='SKU', related='project_id.sku', store=True)
    read_only_close = fields.Boolean(default=False)
    open = fields.Boolean(default=True)

    @api.depends('user_ids', 'child_ids.user_ids', 'project_id.user_id')
    def _compute_alert_users(self):
        for task in self:
            task.add_alert_users()

    def add_alert_users(self):
        users = self.user_ids | self.project_id.user_id
            
        for child_task in self.child_ids:
            users |= child_task.user_ids
        
        self.alert_users = users

    def write(self, vals):
        if 'state' in vals and vals['state'] == '1_done' and not self.parent_id:
            if not self.env.user.has_group('project.group_project_manager'):
                raise AccessError("Solo los managers pueden cambiar el estado a 'Listo'.")

        return super(Task, self).write(vals)

    @api.constrains('alert_hour')
    def _check_alert_hour(self):
        for task in self:
            if task.alert_hour < 0 or task.alert_hour >= 24:
                raise ValidationError("La hora para la alerta debe estar entre 0 y 24 horas.")
    
    @api.constrains('project_id')
    def _check_project_id(self):
        for record in self:
            if record.project_id.open == False:
                raise UserError('El proyecto está cerrado, no se pueden crear tareas')
