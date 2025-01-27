# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    balance_usd = fields.Monetary(
        string='Balance en USD', 
        currency_field='usd_currency_id', 
        compute='_compute_balance_currency', store=True)
    
    usd_currency_id = fields.Many2one(
        'res.currency', 
        string='Moneda USD', 
        default=lambda self: self.env['res.currency'].search([('name', '=', 'USD')], limit=1))

    exchange_rate = fields.Float(
        string='Tipo de cambio',
        compute='_compute_tipo_cambio',
        store=True)

    @api.depends('balance', 'currency_id', 'exchange_rate')
    def _compute_balance_currency(self):
        for line in self:
            if line.exchange_rate != 0:
                line.balance_usd = line.balance / line.exchange_rate
            else:
                line.balance_usd = line.balance
    
    @api.depends('company_id', 'currency_id', 'date', 'td_entry_date')
    def _compute_tipo_cambio(self):
        currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        for record in self:
            if record.td_entry_date:
                #convertir char a date
                date = fields.Date.from_string(record.td_entry_date)
            else:
                date = record.date
            if record.company_id and currency and record.currency_id:
                conversion_rate = self.env['res.currency']._get_conversion_rate(
                    currency,
                    record.company_currency_id,
                    record.company_id,
                    date)
            else:
                conversion_rate = 1
            record.exchange_rate = conversion_rate
    
    #Forzar la actualización de los campos calculados
    def force_update(self):
        records = self.env['account.move.line'].search([])
        for record in records:
            record._compute_tipo_cambio()
