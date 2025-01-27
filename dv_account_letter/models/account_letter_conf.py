# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountLetterConf(models.Model):
    _name = 'account.letter.conf'
    _description = 'Cuentas de Letras'

    account_type = fields.Selection(
        [('asset_receivable', 'Por Cobrar'), 
         ('liability_payable', 'Por Pagar'),
         ("asset_cash", "Banco y efectivo"),
         ("liability_current", "Activos corrientes"),
         ("expense", "Gastos"),
         ("income", "Ingreso"),
         ("income_other", "Otros ingresos"),],
        string='Tipo de Cuenta',
        required=True
    )
    document_type = fields.Selection(
        [('letter', 'Letra'),
         ('retention', 'Retención'),
         ('commission', 'Comisión'),
         ('difference', 'Diferencia de cambio'),],
        default='letter',
        string='Tipo de Documento',
        required=True
    )
    letter_type = fields.Selection(
        selection=[
            ('portfolio', 'En Cartera'),
            ('billing', 'En Cobranza'),
        ],
        string='Tipo de Letra',
    )
    group_id = fields.Many2one(
        'account.group',
        string='Grupo')
    account_id = fields.Many2one(
        'account.account', 
        string='Cuenta',
        domain="[('account_type', '=', account_type),('group_id', '=', group_id)]"
    )
    #Campos extras
    company_id = fields.Many2one(
        'res.company', 
        string='Compañia', 
        default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        'res.currency', 
        string='Moneda',
        default=lambda self: self.env.company.currency_id 
    )
    #Evita que se repita la configuracion de cuentas
    @api.constrains('account_type', 'letter_type', 'currency_id')
    def _check_nro_letter(self):
        for record in self:
            if record.account_type and record.letter_type and record.currency_id:
                account_letter = self.env['account.letter.conf'].search([
                    ('account_type', '=', record.account_type),
                    ('letter_type', '=', record.letter_type),
                    ('currency_id', '=', record.currency_id.id)
                ])
                if len(account_letter) > 1:
                    raise UserError(f'Ya existe la cuenta {self.account_type_t.get(self.account_type)} para el tipo de letra {self.letter_type_t.get(self.letter_type)} y tipo de moneda en {self.currency_id.name}')
    
    #Traducciones
    account_type_t = {
        'asset_receivable': 'Por Cobrar',
        'liability_payable': 'Por Pagar',
    }
    letter_type_t = {
        'portfolio': 'En Cartera',
        'billing': 'En Cobranza',
    }