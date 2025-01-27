from odoo import fields, models, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    subtotal_usd = fields.Monetary(compute='_compute_subtotal_pen_usd')
    currency_usd_id = fields.Many2one('res.currency', string='Currency USD', default=lambda self: self.env.ref('base.USD').id)

    subtotal_pen = fields.Monetary(compute='_compute_subtotal_pen_usd')
    currency_pen_id = fields.Many2one('res.currency', string='Currency PEN', default=lambda self: self.env.ref('base.PEN').id)

    account_date_maturity = fields.Date(
        string='Fecha de Vencimiento',
        compute="_compute_account_date_maturity",
        store=False
    )
  
    @api.depends('unreconciled_aml_ids')
    def _compute_subtotal_pen_usd(self):
        for partner in self:
            subtotal_pen = 0
            subtotal_usd = 0
        
            for move_line in partner.unreconciled_aml_ids:
                subtotal_pen += move_line.amount_pen
                subtotal_usd += move_line.amount_usd
            
            partner.subtotal_usd = subtotal_usd
            partner.subtotal_pen = subtotal_pen

    
    @api.depends('unreconciled_aml_ids', 'unreconciled_aml_ids.date_maturity')
    def _compute_account_date_maturity(self):
        for partner in self:
            i = 0
            if partner and partner.unreconciled_aml_ids:
                minor_date = False
                for line in partner.unreconciled_aml_ids:
                    if line.date_maturity:
                        if i == 0: 
                            minor_date = line.date_maturity
                        elif minor_date > line.date_maturity:
                            minor_date = line.date_maturity
                        i+=1
                partner.account_date_maturity = minor_date

    def _get_unreconciled_aml_domain(self):
        return [
            ('reconciled', '=', False),
            ('account_id.deprecated', '=', False),
            ('account_id.account_type', '=', 'asset_receivable'),
            ('parent_state', '=', 'posted'),
            ('partner_id', 'in', self.ids),
            ('company_id', 'child_of', self.env.company.id),
            ('edi_state', '=', 'sent'),
        ]


    def action_pdf(self):
        return self.env.ref('dv_account_followup_custom.action_report_pdf').report_action(self)
