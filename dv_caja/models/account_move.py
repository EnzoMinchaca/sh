from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'

    caja_id = fields.Many2one('caja.caja', string="Caja", store=True)
    periodo_id = fields.Many2one('caja.periodo', string="Periodo de Caja", store=True)
    secuencia_id = fields.Many2one('caja.secuencia', string="Secuencia de Caja", store=True)
    diario_caja = fields.Many2one('account.journal', string="Diario de Caja", store=True)
    
    partner_name = fields.Char(
        related='partner_id.name', 
        string='Nombre del Proveedor', 
        store=True
    )
    partner_vat = fields.Char(
        related='partner_id.vat', 
        string='Identificación del Proveedor', 
        store=True
    )
    
    #en este create hago que se cree y a la vez se pague, esto solo aplica cuando viene de la caja
    @api.model
    def create(self, vals_list):
        #me aseguro de que sea una lista
        if isinstance(vals_list, dict):  #si es diccionario lo envuelvo en una lista
            vals_list = [vals_list]

        for vals in vals_list:
            #primero valido que sea una factura de proveedor
            if vals.get('move_type') != 'in_invoice':
                #si no es de prov, no cambio nada y se crea la factura nativa
                return super(AccountMove, self).create(vals_list)

            #valido que tenga una caja de contexto la cual se pasara al presionar el boton
            context = self.env.context
            if not context.get('default_caja_id'):
                #si no proviene de una caja, no cambio nada y se crea la factura nativa
                return super(AccountMove, self).create(vals_list)

            #obtengo los fatos del contexto
            caja_id = context.get('default_caja_id')
            periodo_id = context.get('default_periodo_id')
            secuencia_id = context.get('default_secuencia_id')
            saldo_disponible = context.get('default_saldo_disponible')
            saldo_periodo = context.get('default_saldo_periodo')
            diario = context.get('default_diario_caja')

            if 'tax_totals' in vals and 'amount_total' in vals['tax_totals']:
                if saldo_disponible and saldo_disponible < vals['tax_totals']['amount_total']:
                    raise ValidationError("No hay saldo suficiente en la caja para crear la provisión")
                if saldo_periodo and saldo_periodo < vals['tax_totals']['amount_total']:
                    raise ValidationError("No hay saldo suficiente en el periodo de la caja para crear la provisión")

            #le asigo la caja, periodo y secuencia a la factura
            if caja_id:
                vals['caja_id'] = caja_id
            if periodo_id:
                vals['periodo_id'] = periodo_id
            if secuencia_id:
                vals['secuencia_id'] = secuencia_id
            if diario:
                vals['diario_caja'] = diario
        
        #creo la factura
        factura = super(AccountMove, self).create(vals_list)

        #y la publico solo si esta en borrador, ya que debe estar publicada para hacer el pago
        if factura.state == 'draft':
            factura.action_post()

        #genero el pago si la factura está publicada
        if factura.state == 'posted':
            #obtengo el metodo de pago valido para el diario, en este caso seria el tipico "Manual"
            payment_method = factura.diario_caja.inbound_payment_method_line_ids[:1] if factura.move_type == 'out_invoice' else factura.diario_caja.outbound_payment_method_line_ids[:1]
            if not payment_method:
                raise ValidationError("No se encontró un método de pago válido para el diario seleccionado.")
            #es necesario que un pago se cree a partir de una factura sino da error, por eso le agrego este contexto
            payment_register = self.env['account.payment.register'].with_context(
                active_model='account.move',
                active_ids=[factura.id],
            ).create({
                'journal_id': factura.diario_caja.id,  #este es el diario de la caja que pase por contexto y tambien lo guarde en la factura
                'amount': factura.amount_residual,  #monto total pendiente de la factura
                'payment_date': fields.Date.context_today(self),  #fecha del pago
                'communication': factura.name,  #referencia del pago
                'payment_method_line_id': payment_method.id,  #metodo de pago
            })
            
            #ejecuto el metodo que crea y valida los pagos
            payment_register.action_create_payments()
            
            #actualizo el saldo disponible en la caja
            if factura.caja_id:
                nuevo_saldo = factura.caja_id.saldo_disponible - factura.amount_total
                gastos_provisiones = factura.caja_id.gasto_provisiones + factura.amount_total
                nuevo_saldo_periodo = factura.periodo_id.saldo_periodo - factura.amount_total
                nuevo_saldo_periodo_caja = factura.caja_id.saldo_periodo - factura.amount_total
                if nuevo_saldo < 0:
                    raise ValidationError("El saldo disponible no puede ser negativo.")
                factura.caja_id.sudo().write({'saldo_disponible': nuevo_saldo})
                factura.caja_id.sudo().write({'gasto_provisiones': gastos_provisiones})
                factura.periodo_id.sudo().write({'saldo_periodo': nuevo_saldo_periodo})
                factura.caja_id.sudo().write({'saldo_periodo': nuevo_saldo_periodo_caja})

        return factura

    def action_post(self):
        #este es el action_post original, solo que le agregue esta condicion de que si es draft, ya que si por ejemplo
        #en vez de guardar la factura directamente se presionaba confirmar, el post se ejecutaba dos veces, uno en el 
        #create y tambien aca, y eso mostraba un mensaje de error, asi que con esta condicion solo publica si
        #la factura esta como borrador
        if self.state == 'draft':
            moves_with_payments = self.filtered('payment_id')
            other_moves = self - moves_with_payments
            if moves_with_payments:
                moves_with_payments.payment_id.action_post()
            if other_moves:
                other_moves._post(soft=False)
        return False
