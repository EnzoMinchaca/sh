from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

class ReporteCaja(models.Model):
    _name = 'reporte.caja'
    _description = 'Reporte para caja'
    _order = 'id desc'
    
    name = fields.Char(string="Nombre", required=True, store=True, readonly=True)
    reporte_tipo_pago = fields.Selection(
        [('outbound', 'Enviar'), ('inbound', 'Recibir')],
        string="Tipo de Operación",
        required=True,
        store=True,
        readonly=True
    )
    payment_id = fields.Many2one('account.payment', string="Registro de Pago", store=True, readonly=True, ondelete="cascade")
    currency_id = fields.Many2one('res.currency', string="Moneda", required=True, store=True, readonly=True)
    importe = fields.Monetary(string="Importe", currency_field='currency_id', store=True, readonly=True)
    importe_absoluto = fields.Monetary(string="Importe absoluto", currency_field='currency_id', compute='_compute_importe_absoluto', store=True, readonly=True)
    reporte_fecha = fields.Date(string="Fecha", store=True, readonly=True)
    caja_id = fields.Many2one('caja.caja', string="Caja", store=True, readonly=True)
    periodo_id = fields.Many2one('caja.periodo', string="Periodo de Caja", store=True, readonly=True)
    secuencia_id = fields.Many2one('caja.secuencia', string="Secuencia de Caja", store=True, readonly=True)
    move_id = fields.Many2one('account.move', string="Registro de Asiento contable", store=True, readonly=True)
    
    @api.depends('importe')
    def _compute_importe_absoluto(self):
        for record in self:
            record.importe_absoluto = abs(record.importe)