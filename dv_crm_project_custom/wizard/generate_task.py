from odoo import fields, models
import logging
import re
from calendar import monthrange
from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta
from pytz import timezone
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)

class GenerateTask(models.TransientModel):
    _name = 'project.generate.task'
    _description = 'Genarate Task'

    number_tasks = fields.Integer(string='Número de Tareas')

    def action_generate(self):
        user_tz = self.env.user.tz or 'UTC' 
        local_tz = timezone(user_tz)

        project_id = self.env.context.get('default_project_id')
        project = self.env['project.project'].search([('id', '=', project_id)])
        name_template = 'DOC. CONFORMIDAD/PAGO N°'

        if not project_id:
            return

        # Buscar la tarea plantilla en el proyecto específico
        task_model = self.env['project.task']
        template_task = task_model.search([
            ('project_id', '=', project_id),
            ('parent_id', '=', False),
            ('active', '=', True),
            ('name', 'ilike', name_template)
        ], limit=1)
        

        if not template_task:
            raise UserError("No se ha encontrado ninguna tarea plantilla en este proyecto.")

        template_task.generate_task = True

        if not template_task.alert_users:
            template_task.add_alert_users()

        if not template_task.alert_hour:
            template_task.alert_hour = 9.5

        clean_name = re.sub(r'N° \d+', '', template_task.name).strip()

        start_date = template_task.planned_date_begin
        end_date = template_task.date_deadline

        # Crear nuevas tareas basadas en la plantilla
        for i in range(1, self.number_tasks):
            new_task_name = f"{clean_name} N° {i+1}"
            new_task_vals = {
                'name': new_task_name,
                'project_id': template_task.project_id.id,
                'user_ids': [(6, 0, template_task.user_ids.ids)],
                'tag_ids': [(6, 0, template_task.tag_ids.ids)],
                'allocated_hours': template_task.allocated_hours,
                'company_id': template_task.company_id.id,
                'sequence': template_task.sequence, 
                'email_cc': template_task.email_cc,
                'displayed_image_id': template_task.displayed_image_id.id,
                'days_alert': template_task.days_alert if template_task.days_alert > 0 else 3,
                'generate_task': True
            }

            if start_date and end_date:

                start_date_local = (template_task.planned_date_begin).astimezone(local_tz)
                end_date_local = (template_task.date_deadline).astimezone(local_tz)

                template_start_date = start_date_local.replace(year=start_date.year, month=start_date.month, day=start_date.day, hour=start_date.hour, minute=start_date.minute)
                template_end_date = end_date_local.replace(year=end_date.year, month=end_date.month, day=end_date.day, hour=end_date.hour, minute=end_date.minute)

                # Primer caso: Fechas en el mismo mes
                if template_start_date.month == template_end_date.month:
                    new_start_date = template_start_date + relativedelta(months=i)
                    _, ultimo_dia = monthrange(new_start_date.year, new_start_date.month)
                    new_end_date = local_tz.localize(datetime(new_start_date.year, new_start_date.month, ultimo_dia, template_end_date.hour, template_end_date.minute))
                
                # Segundo caso: Fechas en meses diferentes
                else:
                    new_end_date = template_end_date + relativedelta(months=i)
                    new_date = template_start_date + relativedelta(months=i)
                    _, ultimo_dia = monthrange(new_date.year, new_date.month)
                    new_start_date = local_tz.localize(datetime(new_date.year, new_date.month, ultimo_dia, template_start_date.hour, template_start_date.minute))
                    
                new_task_vals.update({
                    'planned_date_begin': fields.Datetime.to_string(new_start_date),
                    'date_deadline': fields.Datetime.to_string(new_end_date),
                })

            new_task = task_model.create(new_task_vals)

            # Copiar subtareas
            for subtask in template_task.child_ids:
                subtask_vals = {
                    'name': subtask.name,
                    'parent_id': new_task.id, 
                    'user_ids': [(6, 0, subtask.user_ids.ids)],
                }
                task_model.create(subtask_vals)
            
            new_task.write({'alert_users': [(6, 0, template_task.alert_users.ids)], 'alert_hour': template_task.alert_hour})

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def schedule_alert_email(self):
        """ Busca Correos Programados """

        tasks = self.env['project.task'].search([('planned_date_begin', '!=', False), ('date_deadline', '!=', False), ('generate_task', '=', True)])

        for task in tasks:
            for user in task.alert_users:

                user_tz = user.tz or 'UTC' 
                local_tz = timezone(user_tz)

                end_date = ((task.date_deadline).astimezone(local_tz)).date()
                alert_hour = task.alert_hour 
                
                days_alert = task.days_alert

                alert_dates = [end_date - timedelta(days=i) for i in range(days_alert - 1, -1, -1)]

                today = ((datetime.now()).astimezone(local_tz)).date()

                if today in alert_dates:
                    self.schedule_email_for_task(task, alert_hour, user, local_tz)

    def schedule_email_for_task(self, task, alert_hour, user, local_tz):
        """ Programa el envío del correo a la hora especificada """

        if isinstance(alert_hour, float):
            hours = int(alert_hour)
            minutes = int(round((alert_hour - hours) * 60))
            alert_hour = time(hours, minutes)

        # Programar el envío del correo a la hora especificada (alert_hour)
        send_time = ((datetime.now()).astimezone(local_tz)).replace(hour=alert_hour.hour, minute=alert_hour.minute, second=0)

        if user.email:

            # Crear el correo programado
            mail = self.env['mail.mail'].sudo().create({
                'subject': f'Alerta de Fecha Límite de { task.name }',
                'email_from': (
                    "odoo.correo@dailytech.pe"
                ),
                'email_to': user.email,
                'body_html': f"""
                    <p><strong>SKU:<strong> { (task.project_id.sku if task.project_id.sku else '') }</p>
                    <p><strong>NEGOCIO:<strong> { task.project_id.display_name }</p>
                    <p><strong>GERENTE DE PROYECTO:<strong> { task.project_id.user_id.name }</p>
                    <p><strong>{ task.name }<strong></p>
                    <p><strong>FECHA LÍMITE:<strong> { (task.date_deadline.astimezone(local_tz)).strftime('%d/%m/%Y') }</p>
                """,
                'auto_delete': False,
                'scheduled_date': send_time,  # Asegúrate de que se establezca la fecha de envío
            })