from odoo import _, api, fields, models



class ResPartnerEconomicActivity(models.Model):
    _name = 'res.partner.economic.activity'
    _description = 'Actividades económicas de contribuyentes'
    
    activity_type = fields.Selection([('Principal', 'Principal'),
                                        ('Secundaria 1', 'Secundaria 1'),
                                        ('Secundaria 2', 'Secundaria 2'),
                                        ('Secundaria 3', 'Secundaria 3'),
                                        ('Secundaria 4', 'Secundaria 4')], string='Tipo de actividad')
    l10n_pe_economic_activity_id = fields.Many2one('l10n_pe.economic.activity', string='Actividad económica')
    code = fields.Char(string='Código', related='l10n_pe_economic_activity_id.code')
    name = fields.Char(string='Nombre', related='l10n_pe_economic_activity_id.name')
    partner_id = fields.Many2one('res.partner', string='Contacto')