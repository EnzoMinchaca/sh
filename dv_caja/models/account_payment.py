from odoo import models, api, fields
from odoo.exceptions import UserError, ValidationError

class AccountPayment(models.Model):
    _inherit = 'account.payment'
    
    caja_id = fields.Many2one('caja.caja', string="Caja", store=True)
    periodo_id = fields.Many2one('caja.periodo', string="Periodo de Caja", store=True)
    secuencia_id = fields.Many2one('caja.secuencia', string="Secuencia de Caja", store=True)
    
    @api.model
    def create(self, vals):
        if vals.get('is_internal_transfer'):
            #diarios de origen y destino
            journal_from = self.env['account.journal'].browse(vals.get('journal_id'))
            journal_to = self.env['account.journal'].browse(vals.get('destination_journal_id'))

            #busco cajas con los diarios
            caja_from = self.env['caja.caja'].search([('diario', '=', journal_from.id)], limit=1)
            caja_to = self.env['caja.caja'].search([('diario', '=', journal_to.id)], limit=1)
            
            user = self.env.user

            # Verificar si el usuario pertenece al grupo "Responsable de Caja"
            group_responsable = self.env.ref('dv_caja.group_caja_responsable')
            group_administrador = self.env.ref('dv_caja.group_caja_administrador')
            
            if group_responsable in user.groups_id and group_administrador not in user.groups_id:
                # Si el usuario es un Responsable de Caja, verificar restricciones
                payment_type = vals.get('payment_type')
                if not (caja_from and caja_to and caja_from.responsable == user and caja_to.responsable == user):
                    if payment_type == 'outbound':
                        if caja_from and caja_from.responsable != user:
                            raise UserError("El usuario responsable de caja no puede realizar una operación de enviar un importe desde una caja que no le fue asignada")
                        if not caja_from and caja_to and caja_to.responsable == user:
                            raise UserError("El usuario responsable de caja no puede realizar una operación de enviar un importe que no sea desde una de sus cajas asignadas")
                    if payment_type == 'inbound':
                        if caja_to and caja_to.responsable != user:
                            raise UserError("El usuario responsable de caja no puede realizar una operación de recibir un importe desde una caja que no le fue asignada")
                        if not caja_to and caja_from and caja_from.responsable == user:
                            raise UserError("El usuario responsable de caja no puede realizar una operación de recibir un importe que no sea desde una de sus cajas asignadas")
            
            if caja_from and not caja_from.periodo_id:
                raise ValidationError("La caja origen debe tener seleccionado un periodo para poder recibir o realizar un pago")
            
            if caja_to and not caja_to.periodo_id:
                raise ValidationError("La caja destino debe tener seleccionado un periodo para poder recibir o realizar un pago")
            
            if caja_from and not caja_from.periodo_id.activo:
                    raise ValidationError("La caja origen debe tener seleccionado un periodo activo para poder recibir o realizar un pago")
                
            if caja_to and not caja_to.periodo_id.activo:
                raise ValidationError("La caja destino debe tener seleccionado un periodo activo para poder recibir o realizar un pago")

            amount = vals.get('amount', 0.0)

            if vals.get('payment_type') == 'outbound' and caja_from:
                if caja_from.saldo_disponible < amount: #si hay caja de destino solo me interesa que pueda enviar
                    raise ValidationError("El saldo de la caja de origen es insuficiente para realizar el pago")
                if caja_from.saldo_periodo < amount:
                    raise ValidationError("El saldo de periodo de la caja de origen es insuficiente para realizar el pago")

            if vals.get('payment_type') == 'inbound' and caja_to:
                if caja_to.saldo_disponible < amount: #si hay caja de destino solo me interesa que pueda enviar tambien
                    raise ValidationError("El saldo de la caja de destino es insuficiente para recibir el pago")
                if caja_to.saldo_periodo < amount:
                    raise ValidationError("El saldo de periodo de la caja de destino es insuficiente para recibir el pago")

        return super(AccountPayment, self).create(vals)

    def action_post(self):
        res = super(AccountPayment, self).action_post()

        for payment in self:
            #si es transferencia interna se trata de envios de plata entre diarios
            if payment.is_internal_transfer:
                #diario de origen y destino
                journal_from = payment.journal_id
                journal_to = payment.destination_journal_id

                #busco cajas con los diarios
                caja_from = self.env['caja.caja'].search([('diario', '=', journal_from.id)], limit=1)
                caja_to = self.env['caja.caja'].search([('diario', '=', journal_to.id)], limit=1)
                
                if caja_from and not caja_from.periodo_id:
                    raise ValidationError("La caja origen debe tener seleccionado un periodo para poder recibir o realizar un pago")
                
                if caja_to and not caja_to.periodo_id:
                    raise ValidationError("La caja destino debe tener seleccionado un periodo para poder recibir o realizar un pago")
                
                if caja_from and not caja_from.periodo_id.activo:
                    raise ValidationError("La caja origen debe tener seleccionado un periodo activo para poder recibir o realizar un pago")
                
                if caja_to and not caja_to.periodo_id.activo:
                    raise ValidationError("La caja destino debe tener seleccionado un periodo activo para poder recibir o realizar un pago")

                if journal_from.currency_id and journal_to.currency_id:
                    if journal_from.currency_id != journal_to.currency_id:
                        #con esto obtengo el monto convertido a la equivalencia si son diarios de distinta moneda
                        amount_converted = journal_from.currency_id._convert(
                            payment.amount,
                            journal_to.currency_id,
                            payment.company_id,
                            fields.Date.today(),
                        )
                    else:
                        amount_converted = payment.amount
                else:
                    #y si no son de distinta mondea me quedo con el monto original
                    amount_converted = payment.amount

                #CAJA ORIGEN PARA AMBAS OPERACIONES
                if caja_from and payment.payment_type == 'outbound':
                    if caja_from.saldo_disponible >= payment.amount:
                        caja_from.saldo_disponible -= payment.amount
                    else:
                        raise ValidationError("El saldo de la caja de origen es insuficiente para realizar el pago")
                    
                    if caja_from.saldo_periodo >= payment.amount:
                        caja_from.saldo_periodo -= payment.amount
                        caja_from.periodo_id.saldo_periodo -= payment.amount
                    else:
                        raise ValidationError("El saldo de periodo de la caja de origen es insuficiente para realizar el pago")
                
                if caja_from and payment.payment_type == 'inbound':
                    caja_from.saldo_disponible += amount_converted
                    caja_from.saldo_periodo += amount_converted
                    caja_from.periodo_id.saldo_periodo += amount_converted
                
                #CAJA DESTINO AMBAS OPERACIONES
                if caja_to and payment.payment_type == 'inbound':
                    if caja_to.saldo_disponible >= payment.amount:
                        caja_to.saldo_disponible -= payment.amount
                    else:
                        raise ValidationError("El saldo de la caja de destino es insuficiente para realizar el pago")
                    
                    if caja_to.saldo_periodo >= payment.amount:
                        caja_to.saldo_periodo -= payment.amount
                        caja_to.periodo_id.saldo_periodo -= payment.amount
                    else:
                        raise ValidationError("El saldo de periodo de la caja de destino es insuficiente para realizar el pago")
                
                if caja_to and payment.payment_type == 'outbound':
                    caja_to.saldo_disponible += amount_converted
                    caja_to.saldo_periodo += amount_converted
                    caja_to.periodo_id.saldo_periodo += amount_converted
                #este otro id de pago se genera como contraparte del pago en el original metodo, asique lo uso para el segundo registro de creacion
                if payment.paired_internal_transfer_payment_id:
                    paired_payment = payment.paired_internal_transfer_payment_id
                    #creo registros de reporte.caja
                    if caja_from and caja_to:
                        #ambos diarios son de caja
                        self.env['reporte.caja'].create({
                            'name': payment.name,
                            'reporte_tipo_pago': 'outbound' if payment.payment_type == 'outbound' else 'inbound',
                            'payment_id': payment.id,
                            'move_id': payment.move_id.id,
                            'currency_id': journal_from.currency_id.id,
                            'importe': -payment.amount if payment.payment_type == 'outbound' else amount_converted,
                            'reporte_fecha': payment.date,
                            'caja_id': caja_from.id,
                            'periodo_id': caja_from.periodo_id.id,
                            'secuencia_id': caja_from.secuencia_id.id,
                        })
                        self.env['reporte.caja'].create({
                            'name': paired_payment.name,
                            'reporte_tipo_pago': 'inbound' if payment.payment_type == 'outbound' else 'outbound',
                            'payment_id': paired_payment.id,
                            'move_id': paired_payment.move_id.id,
                            'currency_id': journal_to.currency_id.id,
                            'importe': paired_payment.amount if paired_payment.payment_type == 'outbound' else amount_converted,
                            'reporte_fecha': paired_payment.date,
                            'caja_id': caja_to.id,
                            'periodo_id': caja_to.periodo_id.id,
                            'secuencia_id': caja_to.secuencia_id.id,
                        })
                    elif caja_from:
                        #solo el diario de origen es de caja
                        self.env['reporte.caja'].create({
                            'name': payment.name,
                            'reporte_tipo_pago': 'outbound' if payment.payment_type == 'outbound' else 'inbound',
                            'payment_id': payment.id,
                            'move_id': payment.move_id.id,
                            'currency_id': journal_from.currency_id.id,
                            'importe': -payment.amount if payment.payment_type == 'outbound' else amount_converted,
                            'reporte_fecha': payment.date,
                            'caja_id': caja_from.id,
                            'periodo_id': caja_from.periodo_id.id,
                            'secuencia_id': caja_from.secuencia_id.id,
                        })
                    elif caja_to:
                        #solo el diario de destino es de caja
                        self.env['reporte.caja'].create({
                            'name': paired_payment.name,
                            'reporte_tipo_pago': 'inbound' if payment.payment_type == 'outbound' else 'outbound',
                            'payment_id': paired_payment.id,
                            'move_id': paired_payment.move_id.id,
                            'currency_id': journal_to.currency_id.id,
                            'importe': paired_payment.amount if paired_payment.payment_type == 'outbound' else amount_converted,
                            'reporte_fecha': paired_payment.date,
                            'caja_id': caja_to.id,
                            'periodo_id': caja_to.periodo_id.id,
                            'secuencia_id': caja_to.secuencia_id.id,
                        })
            else:
                #no es trasnferencia interna, entonces registro basico
                journal = payment.journal_id
                caja = self.env['caja.caja'].search([('diario', '=', journal.id)], limit=1)
                if caja:
                    self.env['reporte.caja'].create({
                        'name': payment.name,
                        'reporte_tipo_pago': payment.payment_type,
                        'payment_id': payment.id,
                        'move_id': payment.move_id.id,
                        'currency_id': journal.currency_id.id,
                        'importe': payment.amount,
                        'reporte_fecha': payment.date,
                        'caja_id': caja.id,
                        'periodo_id': caja.periodo_id.id,
                        'secuencia_id': caja.secuencia_id.id,
                    })

        return res