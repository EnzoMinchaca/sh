# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CrmStage(models.Model):
    _inherit = 'crm.stage'

    order_desc = fields.Boolean(string='Ordenar descendente', default=False)
    order_asc = fields.Boolean(string='Ordenar ascendente', default=False)
    field_by_order = fields.Many2one('ir.model.fields', string='Campo por ordenar',
        domain="[('model_id', '=', 'crm.lead'),('ttype', 'in', ['date', 'datetime'])]")
    field_by_order_name = fields.Char(string='Campo por ordenar', related='field_by_order.name', store=True)

    @api.onchange('order_desc', 'order_asc')
    def _onchange_order(self):
        if self.order_desc and self.order_asc:
            # Si ambos están seleccionados, mantenemos solo el último seleccionado
            self.order_asc = not self.order_desc
