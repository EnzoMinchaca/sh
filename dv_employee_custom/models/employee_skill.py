from odoo import models, fields, api
from datetime import timedelta, date

class HrEmployeeSkill(models.Model):
    _inherit = 'hr.employee.skill'

    archivo = fields.Binary(string="Archivo Adjunto", attachment=True, store=True)
    archivo_nombre = fields.Char(string="Nombre del Archivo", store=True)
    
    puesto = fields.Many2one(
        'hr.job', 
        string="Puesto", 
        related='employee_id.job_id', 
        store=True, 
    )
    fecha_inicio = fields.Date(string="Fecha de Inicio", store=True, readonly=False)
    fecha_fin = fields.Date(string="Fecha de Fin", store=True, readonly=False)
    fecha_renovacion = fields.Date(string="Fecha de Renovación", store=True, readonly=False)
    
    nombre_compania = fields.Char(string="Nombre de compañía", store=True, readonly=False)
    personalizado_texto = fields.Char(string="Genérico texto", store=True, readonly=False)
    personalizado_numerico = fields.Integer(string="Genérico numero", group_operator=False, store=True, readonly=False)
    
    def send_renewal_notification(self):
        #print("Viendo renovaciones")
        today = date.today()
        alertas = self.env['alerta.renovacion'].sudo().search([])

        for alerta in alertas:
            notification_date = today + timedelta(days=alerta.dias)
            #print(f"Revisando alertas con {alerta.dias} días")

            #busco las habilidades que cumplan con la fecha y el empleado asignado
            skills = self.sudo().search([
                ('fecha_renovacion', '<=', notification_date),
                ('employee_id', 'in', alerta.empleados_ids.ids),
            ])
            #print(f"Habilidades próximas: {skills}")

            for skill in skills:
                employee = skill.employee_id
                if employee and employee.work_email:
                    #print(f"Notificando a {employee.name} ({employee.work_email})")
                    template = self.env.ref('dv_employee_custom.email_template_renovacion')
                    template.send_mail(skill.id, force_send=True)   #envio el mail al correo del empleado