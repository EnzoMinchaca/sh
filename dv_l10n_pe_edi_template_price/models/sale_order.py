from odoo import _, api, fields, models
from odoo.tools import float_round, html_escape
from odoo.exceptions import UserError
import num2words

class AccountMove(models.Model):
    _inherit = 'sale.order'


    # Importe en moneda con formato nacional PE:
    amount_total_text = fields.Char(
        string='Monto total en letras',
        compute='_compute_amount_text',
    )


    date_order_custom = fields.Date(string='Fecha de Orden',compute='_compute_get_date_order')

    @api.depends('date_order')
    def _compute_get_date_order(self):
        for record in self:
            record.date_order_custom = record.date_order.strftime('%Y-%m-%d') if record.date_order else '----'
    
    CURRENCY_TRANSLATIONS = {
        'USD': 'Dólares',
        'PEN': 'Soles',
        'EUR': 'Euros',
    }
    
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
    
    def _get_report_base_filename(self):
        res = super()._get_report_base_filename()
        if self.company_id.country_id.code == 'PE':
            res = 'dv_l10n_pe_edi_template_price.report_pe_price_document'
        return res