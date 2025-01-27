# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError
from datetime import timedelta
import base64
import num2words

class AccountLetterLine(models.Model):
    _inherit = 'account.letter.line'

    amount_total_text = fields.Char(
        string='Monto total en letras',
        compute='_compute_amount_text',
    )
    
    CURRENCY_TRANSLATIONS = {
        'USD': 'Dólares',
        'PEN': 'Soles',
        'EUR': 'Euros',
    }
    def generate_label_pdf(self):
        return self.env.ref('dv_account_letter_template.action_report_letter').report_action(self)
    
    @api.depends('amount_total', 'currency_id')
    def _compute_amount_text(self):
        for record in self:
            if record.amount_total and record.currency_id:
                # Convertir amount_total a palabras
                amount_total_numero = int(record.amount_total)  # Obtener la parte entera del amount_total
                amount_total_decimal = round((record.amount_total - amount_total_numero) * 100)  # Obtener la parte decimal
                amount_total_texto = num2words.num2words(amount_total_numero, lang='es').capitalize()  # Convertir parte entera a palabras
                if amount_total_decimal > 0:
                    amount_total_texto += f' con {amount_total_decimal:02d}/100'  # Agregar parte decimal si existe
                currency_name_translated = self.CURRENCY_TRANSLATIONS.get(record.currency_id.name, record.currency_id.currency_unit_label)
                amount_total_texto += f' {currency_name_translated}'  # Agregar nombre de la moneda
                record.amount_total_text = amount_total_texto.upper()
            else:
                record.amount_total_text = ''