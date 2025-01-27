from odoo import fields, models, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    reconciled_aml_ids = fields.One2many('account.move.line', compute='_compute_reconciled_aml_ids', readonly=False)

    @api.depends('invoice_ids')
    @api.depends_context('company', 'allowed_company_ids')
    def _compute_reconciled_aml_ids(self):
        values = {
            partner.id: line_ids
            for partner, line_ids in self.env['account.move.line']._read_group(
                domain=self._get_reconciled_aml_domain(),
                groupby=['partner_id'],
                aggregates=['id:array_agg'],
            )
        }
        for partner in self:
            partner.reconciled_aml_ids = values.get(partner.id, False)

    def _get_reconciled_aml_domain(self):
        return [
            ('reconciled', '=', True),
            ('account_id.deprecated', '=', False),
            ('account_id.account_type', '=', 'asset_receivable'),
            ('move.payment_state', '=', 'paid'),
            ('parent_state', '=', 'posted'),
            ('partner_id', 'in', self.ids),
            ('company_id', 'child_of', self.env.company.id),
        ]
    