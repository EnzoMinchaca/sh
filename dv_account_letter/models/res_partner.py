# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    total_due = fields.Monetary(
        compute='_compute_total_due',
        groups='account.group_account_readonly,account.group_account_invoice,dv_account_letter.group_tesorery')
    total_overdue = fields.Monetary(
        compute='_compute_total_due',
        groups='account.group_account_readonly,account.group_account_invoice,dv_account_letter.group_tesorery')
    followup_status = fields.Selection(
        [('in_need_of_action', 'Se necesita realizar una acción'), ('with_overdue_invoices', 'Con facturas atrasadas'), ('no_action_needed', 'No necesita realizar una acción')],
        compute='_compute_followup_status',
        string='Estado del seguimiento',
        search='_search_status',
        groups='account.group_account_readonly,account.group_account_invoice,dv_account_letter.group_tesorery')
    followup_line_id = fields.Many2one(
        comodel_name='account_followup.followup.line',
        string="Nivel de seguimiento",
        compute='_compute_followup_status',
        inverse='_set_followup_line_on_unreconciled_amls',
        search='_search_followup_line',
        groups='account.group_account_readonly,account.group_account_invoice,dv_account_letter.group_tesorery')
    followup_responsible_id = fields.Many2one(
        comodel_name='res.users',
        string='Responsable',
        help="El responsable asignado a las actividades de seguimiento manual, si se definen en el nivel.",
        tracking=True,
        copy=False,
        company_dependent=True,
        groups='account.group_account_readonly,account.group_account_invoice,dv_account_letter.group_tesorery')