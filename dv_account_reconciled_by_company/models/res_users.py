# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    reconcile_companies = fields.Many2many(
        'res.company', 
        string='Compañías disponibles para conciliación', 
        compute='_compute_reconcile_companies',
        store=False
    )

    # @api.depends('company_ids', 'company_ids.reconcile_company_child_ids')
    @api.depends_context('allowed_company_ids')
    def _compute_reconcile_companies(self):
        for user in self:
            # Obtener las compañías activas desde el contexto
            allowed_company_ids = self.env.context.get('allowed_company_ids', [])

            # Inicializar un set para evitar duplicados
            all_companies = set(allowed_company_ids)

            # Iterar sobre cada compañía activa y agregar las compañías de conciliación
            companies = self.env['res.company'].browse(allowed_company_ids)
            for company in companies:
                all_companies.update(company.reconcile_company_child_ids.ids)

            # Asignar el resultado a la Many2many `reconcile_companies`
            user.reconcile_companies = [(6, 0, list(all_companies))]