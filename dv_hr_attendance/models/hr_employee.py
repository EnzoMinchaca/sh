# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    vendor = fields.Char(string='Vendor')
    #Evita que se repita el vendor
    @api.constrains('vendor')
    def _check_vendor(self):
        for record in self:
            if record.vendor and self.search_count([('vendor', '=', record.vendor)]) > 1:
                #Busca el nombre y código del empleado con el vendor
                employee = self.search([('vendor', '=', record.vendor), ('id', '!=', record.id)])
                raise ValidationError('El código vendor debe ser único, ya existe un empleado con este código. Nombre: %s, Vendor: %s' % (employee.name, employee.vendor))
