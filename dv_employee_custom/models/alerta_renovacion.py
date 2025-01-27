from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AlertaRenovacion(models.Model):
    _name = 'alerta.renovacion'
    _description = 'Alerta de Renovación'

    name = fields.Char(string="Alerta de Renovación", store=True, default="Alerta de Renovación")
    dias = fields.Integer(string="Días", required=True, store=True)
    empleados_ids = fields.Many2many(
        'hr.employee',
        string="Empleados Asignados",
        store=True
    )

    @api.model
    def get_or_create_alerta_renovacion_action(self):
        #buscar el regitro de alerta, solo es uno asi el limit es opcional
        alerta = self.search([], limit=1)
        if not alerta:
            #lo creo si no existe
            alerta = self.create({'dias': 4})

        #con esto retorno la accion que me llevara al formulario
        return {
            'type': 'ir.actions.act_window',
            'name': 'Alerta Renovación',
            'res_model': 'alerta.renovacion',
            'view_mode': 'form',
            'res_id': alerta.id,  #y con esto abro el registro especifico
            'target': 'current',
        }
