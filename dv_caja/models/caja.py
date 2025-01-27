from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

class Caja(models.Model):
    _name = 'caja.caja'
    _description = 'Modelo para una caja'
    
    name = fields.Char(string="Nombre caja", required=True, store=True)
    cod = fields.Char(string="Código caja", required=True, store=True)
    responsable = fields.Many2one('res.users', string="Responsable", required=True, store=True)
    currency_id = fields.Many2one('res.currency', string="Moneda", required=True, compute="_compute_currency_diario", store=True)
    saldo_disponible = fields.Monetary(string="Saldo disponible", currency_field='currency_id', store=True)
    saldo_periodo = fields.Monetary(string="Saldo periodo", compute="_compute_saldo_periodo", store=True)
    gasto_provisiones = fields.Monetary(string="Gasto en provisiones", store=True)
    diario = fields.Many2one(
        'account.journal', 
        string="Diario",
        required=True,
        domain=lambda self: [
            ('es_de_caja', '=', True),
            ('usado_en_caja', '=', False),
        ],
        store=True)
    periodo_id = fields.Many2one(
        'caja.periodo',
        string="Periodo",
        domain="[('caja_id', '=', id)]",  #filtro los periodos de la caja
        #store=False
    )
    secuencia_id = fields.Many2one(
        'caja.secuencia',
        string="Secuencia",
        domain="[('periodo_id', '=', periodo_id)]",  #filtro las secuencias del periodo seleccionado
        #store=False
    )
    facturas_ids = fields.Many2many(
        'account.move',
        string="Provisiones",
        compute="_factura_secuencia"
    )
    es_admin = fields.Boolean(string="Es admin", compute="_compute_es_admin", default=lambda self: self.env.user.has_group("dv_caja.group_caja_administrador"))

    #valido si es administrador o no
    def _compute_es_admin(self):
        for record in self:
            if record.env.user.has_group("dv_caja.group_caja_administrador"):
                record.es_admin = True
            else:
                record.es_admin = False
    
    @api.depends('periodo_id')
    def _compute_saldo_periodo(self):
        for record in self:
            if record.periodo_id:
                #si hay un perido muestro su salfo en el campo
                record.saldo_periodo = record.periodo_id.saldo_periodo
            else:
                #si no siempre 0
                record.saldo_periodo = 0.0

    @api.model
    def create(self, vals):
        record = super(Caja, self).create(vals)
        #cuando creo una caja, seteo al diario como que esta usado en una caja
        if 'diario' in vals and vals['diario']:
            journal = self.env['account.journal'].browse(vals['diario'])
            journal.usado_en_caja = True
        return record

    def write(self, vals):
        if 'diario' in vals:
            for record in self:
                #si cambia el diario, libero al anterior
                if record.diario and record.diario.id != vals['diario']:
                    record.diario.usado_en_caja = False
                
                #y marco como usado al seleccionado
                if vals['diario']:
                    new_journal = self.env['account.journal'].browse(vals['diario'])
                    new_journal.usado_en_caja = True

        return super(Caja, self).write(vals)

    def unlink(self):
        for record in self:
            #si borro la caja libero al diario, poco probable que se borre la caja pero por las dudas
            if record.diario:
                record.diario.usado_en_caja = False
        return super(Caja, self).unlink()
    
    @api.depends('secuencia_id')
    def _factura_secuencia(self):
        if self.secuencia_id:
            facturas = self.env['account.move'].search([
                #('caja_id', '=', self.id),
                ('periodo_id', '=', self.periodo_id.id),
                ('secuencia_id', '=', self.secuencia_id.id),
                ('move_type', '=', 'in_invoice')
            ])
            self.facturas_ids = [(6, 0, facturas.ids)]  #le asigno las encontradas
        else:
            self.facturas_ids = [(5, 0, 0)]  #si no hay datos limpio todo

    @api.onchange('periodo_id', 'secuencia_id')
    def _onchange_facturas(self):
        #actualizo las facturas cuando cambie el periodo o secuencia
        if self.periodo_id and self.secuencia_id:
            facturas = self.env['account.move'].search([
                #('caja_id', '=', self.id),
                ('periodo_id', '=', self.periodo_id.id),
                ('secuencia_id', '=', self.secuencia_id.id),
                ('move_type', '=', 'in_invoice')
            ])
            self.facturas_ids = [(6, 0, facturas.ids)]  #le asigno las encontradas
        else:
            self.facturas_ids = [(5, 0, 0)]  #si no hay datos limpio todo
    
    @api.onchange('periodo_id')
    def check_periodo_id(self):
        #si no hay periodo limpio el campo secuencia
        if not self.periodo_id or (self.secuencia_id and self.secuencia_id.periodo_id != self.periodo_id):
            self.secuencia_id = False
    
    @api.depends('diario')
    def _compute_currency_diario(self):
        #pongo la moneda del diario seleccionado, sino tiene pongo la de la compañia
        for record in self:
            if record.diario:
                record.currency_id = record.diario.currency_id
            else:
                record.currency_id = self.env.company.currency_id
    
    #abro la creacion de una provision pasandole los datos necesarios
    def action_open_invoice_form(self):
        if not self.secuencia_id and not self.periodo_id:
            raise ValidationError("Se debe de tener un periodo y secuencia seleccionados")
        if not self.periodo_id.activo:
            raise ValidationError("No se pueden realizar operaciones para el periodo seleccionado porque ya cerró")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Factura de Proveedor',
            'res_model': 'account.move',
            'view_mode': 'form',
            'context': {
                'default_move_type': 'in_invoice',  #factura de proveedor
                'default_currency_id': self.currency_id.id,  #moneda de la caja
                'default_ref': self.name,  #moneda de la caja
                #'default_partner_id': 51,  #PARA PRUEBAS SOLO
                'default_caja_id': self.id,
                'default_periodo_id': self.periodo_id.id,
                'default_secuencia_id': self.secuencia_id.id,
                'default_invoice_date': fields.Date.context_today(self),
                'default_saldo_disponible': self.saldo_disponible,
                'default_saldo_periodo': self.saldo_periodo,
                'default_diario_caja': self.diario.id
            },
        }
    
    #este metodo es por si para el ingreso se quiere el comportamiento de nueva transaccion del tablero
    # def action_caja_new_transaction(self):
    #     if not self.periodo_id:
    #         raise ValidationError("Se debe de tener un periodo seleccionado para realizar la acción")
    #     if not self.periodo_id.activo:
    #         raise ValidationError("No se pueden realizar operaciones para el periodo seleccionado porque ya cerró")
    #     return self.diario.action_new_transaction()
    
    #metodo para recibir dinero mediante registro de pagos
    def action_caja_new_transaction(self):
        self.ensure_one()  #me aseguro de que el metodo se ejecute solo para un registro
        if not self.periodo_id:
            raise ValidationError("Se debe de tener un periodo seleccionado para realizar la acción")
        if not self.periodo_id.activo:
            raise ValidationError("No se pueden realizar operaciones para el periodo seleccionado porque ya cerró")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Crear Pago',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'context': {
                'default_journal_id': self.diario.id,
                'default_currency_id': self.currency_id.id,
                'default_is_internal_transfer': True,
                'default_payment_type': 'inbound',
            },
        }
    
    #metodo para enviar dinero mediante registro de pagos
    def action_open_payment_form(self):
        self.ensure_one()  #me aseguro de que el metodo se ejecute solo para un registro
        if not self.periodo_id:
            raise ValidationError("Se debe de tener un periodo seleccionado para realizar la acción")
        if not self.periodo_id.activo:
            raise ValidationError("No se pueden realizar operaciones para el periodo seleccionado porque ya cerró")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Crear Pago',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'context': {
                'default_journal_id': self.diario.id,
                'default_currency_id': self.currency_id.id,
                'default_is_internal_transfer': True,
                'default_payment_type': 'outbound',
            },
        }