from odoo import _, api, fields, models


class ResPartnerRelatedBranch(models.Model):
    _name = 'res.partner.related.branch'
    _description = 'Local anexos'
    
    name = fields.Char(string='Nombre', compute='_compute_name', store=True)
    
    @api.depends('code', 'branch_type')
    def _compute_name(self):
        for record in self:
            record.name = f'{record.code} - {record.branch_type}'
    
    code = fields.Char(string='Código', required=True)
    branch_type = fields.Char(string='Tipo de establecimiento', required=True)
    l10n_pe_economic_activity_id = fields.Many2one('l10n_pe.economic.activity', string='Actividad económica')
    street = fields.Char(string='Dirección')
    partner_id = fields.Many2one('res.partner', string='Empresa')