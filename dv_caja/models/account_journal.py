from odoo import fields, api, models, _
from odoo.exceptions import UserError, ValidationError
import re

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    es_de_caja = fields.Boolean(string="Es de caja", store=True)
    usado_en_caja = fields.Boolean(string="Usado en Caja", store=True)
    
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})

        if not self.code or not isinstance(self.code, str):
            raise UserError(_("El campo 'code' no es válido o no está definido para el diario '%s'. Verifique antes de duplicar." % (self.name or '')))

        read_codes = self.env['account.journal'].with_context(active_test=False).search_read(
            self.env['account.journal']._check_company_domain(self.company_id),
            ['code'],
        )
        all_journal_codes = {code_data['code'] for code_data in read_codes}

        copy_code = self.code
        code_prefix = re.sub(r'\d+', '', self.code).strip()
        counter = 1
        while counter <= len(all_journal_codes) and copy_code in all_journal_codes:
            counter_str = str(counter)
            copy_prefix = code_prefix[:self._fields['code'].size - len(counter_str)]
            copy_code = ("%s%s" % (copy_prefix, counter_str))
            counter += 1

        if counter > len(all_journal_codes):
            raise UserError(_("No se pudo generar un código único automáticamente. Por favor, cree uno manualmente."))

        #este es el metodo original del copy, solo le agrego setear la caja en falso por si se copia una que lo tiene en true
        default.update({
            'code': copy_code,
            'name': _("%s (copy)", self.name or ''),
            'usado_en_caja': False,
        })

        return super(AccountJournal, self).copy(default)

    
class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'
    
    #este es el metodo de nueva transaccion al cerrar y guardar
    def action_save_close(self):
        result = super(AccountBankStatementLine, self).action_save_close()

        for line in self:
            #busco la caja
            caja = self.env['caja.caja'].search([('diario', '=', line.journal_id.id)], limit=1)
            if caja:
                #actualizo los saldos
                caja.saldo_disponible += line.amount
                caja.saldo_periodo += line.amount
                caja.periodo_id.saldo_periodo += line.amount
        return result
    
    def action_save_new(self):
        action = super(AccountBankStatementLine, self).action_save_new()
        for line in self:
            #busco la caja
            caja = self.env['caja.caja'].search([('diario', '=', line.journal_id.id)], limit=1)
            if caja:
                #actualizo los saldos
                caja.saldo_disponible += line.amount
                caja.saldo_periodo += line.amount
                caja.periodo_id.saldo_periodo += line.amount
        return action
    
    def write(self, vals):
        # OVERRIDE

        res = super().write(vals)
        self._synchronize_to_moves(set(vals.keys()))
        #lo de arriba ya estaba por defecto, lo de abajo es lo nuevo
        journal = self.journal_id
        caja = self.env['caja.caja'].search([('diario', '=', journal.id)], limit=1)
        
        if caja and not caja.periodo_id:
            raise ValidationError("La caja debe tener seleccionado un periodo para poder recibir o realizar un pago")
        
        if caja and not caja.periodo_id.activo:
            raise ValidationError("La caja debe tener seleccionado un periodo activo para poder recibir o realizar un pago")
        #solo creo si esta posteada ya que primero se ejecuta dos veces, una en borrador y otra en posteada, sino se crearian dos registros con diferente estado
        if self.move_id.state == 'posted':
            if caja and self.amount > 0:
                self.env['reporte.caja'].create({
                    'name': self.move_id.name,
                    'reporte_tipo_pago': 'inbound',
                    'payment_id': None,
                    'move_id': self.move_id.id,
                    'currency_id': journal.currency_id.id,
                    'importe': self.amount,
                    'reporte_fecha': self.move_id.create_date,
                    'caja_id': caja.id,
                    'periodo_id': caja.periodo_id.id,
                    'secuencia_id': caja.secuencia_id.id,
                })
            if caja and self.amount < 0:
                self.env['reporte.caja'].create({
                    'name': self.move_id.name,
                    'reporte_tipo_pago': 'outbound',
                    'payment_id': None,
                    'move_id': self.move_id.id,
                    'currency_id': journal.currency_id.id,
                    'importe': self.amount * -1,
                    'reporte_fecha': self.move_id.create_date,
                    'caja_id': caja.id,
                    'periodo_id': caja.periodo_id.id,
                    'secuencia_id': caja.secuencia_id.id,
                })
        return res