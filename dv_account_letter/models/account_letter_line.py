# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import timedelta

class AccountLetterLine(models.Model):
    _name = 'account.letter.line'
    _description = 'Línea de Canje de Letras'

    name = fields.Char(
        string='Nombre',
        compute='_compute_name',
        store=True,
    )
    sequence = fields.Integer(
        string='Secuencia',
    )
    is_selected = fields.Boolean(
        string='Seleccionado',
    )
    letter_id = fields.Many2one(
        'account.letter',
        string='Canje',
    )
    letter_type = fields.Selection(
        selection=[
            ('portfolio', 'En Cartera'),
            ('billing', 'En Cobranza'),
        ],
        default='billing',
        string='Tipo de Letra',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Socio',
        related='letter_id.partner_id', store=True,
    )
    move_invoice_type = fields.Selection([
        ('out_invoice', 'Cliente'),
        ('in_invoice', 'Proveedor')],
        string='Tipo',
        related='letter_id.type',
    )
    state = fields.Selection(
        string='Estado',
        related='letter_id.state',
    )
    letter_user_id = fields.Many2one(
        'res.users', 
        string='Vendedor', 
        default=lambda self: self.env.user
    )
    nro_letter = fields.Char(
        string='Nro. de Letra',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        related='letter_id.company_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        related='letter_id.currency_id',
    )
    bank_id = fields.Many2one(
        'res.bank', 
        string='Banco', 
    )
    code = fields.Char(
        string='Código', 
    )
    account_id = fields.Many2one(
        'account.account',
        string='Cuenta',
        index=True, store=True,
        compute='_compute_account_id',
    )
    expiration_date = fields.Date(
        string='Fecha Vencimiento',
        required=True,
    )
    range_date = fields.Integer(
        string='Rango de Días',
        default=0,
    )
    amount_total = fields.Monetary(
        string='Importe',
        currency_field='currency_id',
    )
    commission = fields.Monetary(
        string='Comisión',
        currency_field='currency_id',
    )
    payment_state = fields.Selection(
        selection=[
            ('pending', 'No pagado'),
            ('paid', 'Pagado'),
            ('renewed', 'Renovado'),
            ('protested', 'Protestado'),
            ('refinanced', 'Refinanciado'),
            ('cancelled', 'Cancelado'),
        ],
        string='Estado',
        default='pending',
    )
    payment_id = fields.Many2one(
        'account.payment',
        string='Pago',
    )

    #Evitar crear letras con el mismo número para el mismo socio
    @api.constrains('nro_letter', 'partner_id')
    def _check_nro_letter(self):
        for record in self:
            if record.nro_letter:
                letter = self.env['account.letter.line'].search([
                    ('nro_letter', '=', record.nro_letter),
                    ('partner_id', '=', record.partner_id.id),
                    ('id', '!=', record.id)
                ])
                if letter:
                    raise UserError(f'Ya existe la letra: {letter.name} para el socio: {letter.partner_id.name}')

    @api.depends('nro_letter')
    def _compute_name(self):
        for record in self:
            if record.nro_letter:
                record.name = record.nro_letter
            else:
                record.name = 'Nueva Letra'

    #Configuración de Cuentas
    @api.depends('move_invoice_type')
    def _compute_account_id(self):
        for record in self:
            if record.move_invoice_type == 'in_invoice':
                account_type = 'liability_payable'
            elif record.move_invoice_type == 'out_invoice':
                account_type = 'asset_receivable'
            else:
                return
            if record.letter_type:
                letter_type = record.letter_type
            else:
                letter_type = 'portfolio'
            invoice_account = self.env['account.letter.conf'].search([
                ('account_type', '=', account_type),
                ('document_type', '=', 'letter'),
                ('letter_type', '=', letter_type),
                ('currency_id', '=', record.currency_id.id)
            ], limit=1)
            if invoice_account:
                record.account_id = invoice_account.account_id.id
            else:
                raise UserError('No se encontró una cuenta para la letra')
    
    # Método para abrir la vista previa de pago
    def action_open_preview_payment(self):
        return {
            'name': 'Pago de letra',
            'type': 'ir.actions.act_window',
            'res_model': 'preview.payment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_letter_line_id': self.id,
            },
        }
    
    # Método para incrementar el rango de días
    @api.onchange('range_date')
    def _onchange_range_date(self):
        if self.letter_id.letter_end_date:
            date = self.letter_id.letter_end_date
            self.expiration_date = date + timedelta(days=self.range_date)
    
    def unlink(self):
        for record in self:
            if record.state not in ['draft', 'checked']:
                raise UserError('No se puede eliminar la letra una vez confirmada')
        return super(AccountLetterLine, self).unlink()
    
    def create(self, vals):
        if isinstance(vals, list):
            for val in vals:
                if val.get('letter_id'):
                    letter = self.env['account.letter'].browse(val['letter_id'])
                    if letter.state != 'draft':
                        raise UserError('No se pueden agregar letras a un canje confirmado')
        else:
            if vals.get('letter_id'):
                letter = self.env['account.letter'].browse(vals['letter_id'])
                if letter.state != 'draft':
                    raise UserError('No se pueden agregar letras a un canje confirmado')
        return super(AccountLetterLine, self).create(vals)