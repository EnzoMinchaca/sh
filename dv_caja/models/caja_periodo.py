from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

class CajaPeriodo(models.Model):
    _name = 'caja.periodo'
    _description = 'Modelo para el periodo de una caja'
    _order = 'create_date desc'
    
    name = fields.Char(string="Periodo", store=True)
    caja_id = fields.Many2one('caja.caja', string="Caja", required=True)  # Relación obligatoria con Caja
    secuencia_ids = fields.One2many('caja.secuencia', 'periodo_id', string="Secuencias")
    saldo_periodo = fields.Monetary(string="Saldo periodo", currency_field='currency_id', store=True)
    currency_id = fields.Many2one(related='caja_id.currency_id', string="Moneda", readonly=True, store=True)
    activo = fields.Boolean(sting="Activo", store=True, default=True)
    
    @api.model
    def create(self, vals):
        #el id de la caja solo aparece en el contexto
        caja_id = self._context.get('default_caja_id')
        if caja_id:
            #cierro periodos anteriores pertenecientes a esta caja
            self.env['caja.periodo'].search([('caja_id', '=', caja_id), ('activo', '=', True)]).write({'activo': False})
            #y como es nuevo periodo tendra el saldo igual al del total
            caja = self.env['caja.caja'].browse(caja_id)
            vals['saldo_periodo'] = caja.saldo_disponible
        
        return super(CajaPeriodo, self).create(vals)