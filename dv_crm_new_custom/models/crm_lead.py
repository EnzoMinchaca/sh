from odoo import api, fields, models
from datetime import timedelta
from odoo.exceptions import ValidationError

class Lead(models.Model):
    _inherit = "crm.lead"
    
    sku_anterior = fields.Char(string="SKU Anterior", readonly=True)
    
    def write(self, vals):
        #Cuando se modifica en la vista kanban a este estado valido las fechas
        if 'stage_id' in vals:
            ofertado_stage = self.env['crm.stage'].search([('name', '=', 'Ofertado (C)')], limit=1)
            if vals['stage_id'] == ofertado_stage.id:
                now = fields.Datetime.now()
                for lead in self:
                    if hasattr(self, 'x_studio_plazo_maximo_calendario'):
                        if (now - lead.x_studio_plazo_maximo_calendario) >= timedelta(days=30):  #if (now - lead.create_date).total_seconds() >= 5:  #para probar con 5 segundos
                            lead._mark_as_lost()
                    else:
                        if (now - lead.create_date) >= timedelta(days=30):  #if (now - lead.create_date).total_seconds() >= 5:  #para probar con 5 segundos
                            lead._mark_as_lost()
        return super(Lead, self).write(vals)
    
    def check_and_update_stage(self):
        now = fields.Datetime.now()
        ofertado_stage = self.env['crm.stage'].search([('name', '=', 'Ofertado (C)')], limit=1)
        if ofertado_stage:
            if hasattr(self, 'x_studio_plazo_maximo_calendario'):
                leads = self.search([('stage_id', '=', ofertado_stage.id), ('x_studio_plazo_maximo_calendario', '!=', False)])
            else:
                leads = self.search([('stage_id', '=', ofertado_stage.id), ('create_date', '!=', False)])
            for lead in leads:
                if hasattr(self, 'x_studio_plazo_maximo_calendario'):
                    if (now - lead.x_studio_plazo_maximo_calendario) >= timedelta(days=30):  #if (now - lead.create_date).total_seconds() >= 5:  #para probar con 5 segundos
                        lead._mark_as_lost()
                else:
                    if (now - lead.create_date) >= timedelta(days=30):  #if (now - lead.create_date).total_seconds() >= 5:  #para probar con 5 segundos
                        lead._mark_as_lost()

    def _mark_as_lost(self):
        #Buscar o crear la razon si es que no existe
        text_lost = 'Vigencia de propuesta mayor a 30 dias'
        lost_reason = self.env['crm.lost.reason'].search([
            ('name', '=', text_lost.upper())
        ], limit=1)
        if not lost_reason:
            lost_reason = self.env['crm.lost.reason'].create({
                'name': text_lost.upper()
            })
        
        #Marco la lead como perdida
        lead_lost_wizard = self.env['crm.lead.lost'].create({
            'lead_ids': [(6, 0, [self.id])],
            'lost_reason_id': lost_reason.id,
        })
        lead_lost_wizard.action_lost_reason_apply()

    #con esto valido el sku ingresado para ver si no esta repetido o es valido
    @api.constrains('sku')
    def _check_sku_constraints(self):
        for record in self:
            if not record.sku or len(record.sku) != 9:
                raise ValidationError("El SKU debe tener exactamente 9 caracteres.")

            #me quedo con los primeros 6 caracteres añoMesCodigo
            prefix = record.sku[:6]

            #me fiho que la parte del codigo sea valida
            terminaciones_validas = ["LG", "CE", "SC", "LP", "DP"]
            if prefix[-2:] not in terminaciones_validas:
                raise ValidationError("El SKU debe contener con una nomenclatura válida (LG, CE, SC, LP, DP).")

            #busco el ultimo sku que coincida con el mes y codigo
            registros_filtrados = self.sudo().search(
                [
                    ('sku', '=like', f'{prefix}%'),
                    ('id', '!=', record.id)  #y aca no cuento al actual sino siempre va a aparecer este
                ],
                order='sku desc',
                limit=1
            )

            #si encontre uno me quedo con ese sino es el diaMesCodigo escrito mas 000
            if registros_filtrados:
                record.sku_anterior = registros_filtrados.sku
            else:
                record.sku_anterior = f"{prefix}000"

            #validar si este sku ya existe o no
            duplicado_completo = self.sudo().search(
                [
                    ('sku', '=', record.sku),
                    ('id', '!=', record.id)  #excluyo al actual otra vez
                ],
                limit=1
            )
            if duplicado_completo:
                raise ValidationError(
                    f"El SKU ingresado '{record.sku}' ya existe en otro registro."
                )

            #y que no se guarde si termina con 000 
            if record.sku.endswith('000'):
                raise ValidationError(
                    "No se puede guardar un SKU con terminación '000'. Ingrese un SKU válido."
                )

