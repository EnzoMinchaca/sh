from odoo import models, fields, api

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"
    _order = "date desc, id desc"

    guia_remision = fields.Char(string="Guía de Remisión", compute='_compute_guia_remision', store=True)
    saldo_total = fields.Integer(string="Saldo Total", compute='_compute_saldo_total', store=True)

    @api.depends('picking_id.l10n_latam_document_number')
    def _compute_guia_remision(self):
        for record in self:
            # Verificamos si el picking tiene un número de documento de guía de remisión
            record.guia_remision = record.picking_id.l10n_latam_document_number or ''

    @api.depends('product_id', 'date', 'location_id', 'location_dest_id', 'state')
    def _compute_saldo_total(self):
        for record in self:
            # Si el movimiento no está en estado "hecho", no consideramos el movimiento
            if record.state != 'done':
                record.saldo_total = 0
                continue

            # Dominio para obtener todos los movimientos anteriores o iguales del mismo producto
            domain = [
                ('product_id', '=', record.product_id.id),
                ('state', '=', 'done'),
                ('date', '<=', record.date),
            ]
            # Obtener todos los movimientos anteriores al movimiento actual, ordenados por fecha
            moves = self.env['stock.move.line'].search(domain, order='date asc, id asc')

            saldo_total = 0
            for move in moves:
                if move.location_id.usage == 'internal' and move.location_dest_id.usage != 'internal':
                    # El producto sale de existencias
                    saldo_total -= move.quantity
                elif move.location_id.usage != 'internal' and move.location_dest_id.usage == 'internal':
                    # El producto ingresa a existencias
                    saldo_total += move.quantity

            # Asignar el saldo total calculado al registro actual
            record.saldo_total = saldo_total