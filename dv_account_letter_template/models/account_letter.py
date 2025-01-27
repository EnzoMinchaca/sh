# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import timedelta

class AccountLetter(models.Model):
    _inherit = 'account.letter'

    is_printed = fields.Boolean(
        string='Impreso',
        compute='_compute_is_printed',
    )
    related_invoice_names = fields.Char(
        string='Facturas Relacionadas',
        compute='_compute_related_invoice_names',
        store=True
    )

    @api.depends('letter_line_ids.is_selected')
    def _compute_is_printed(self):
        for rec in self:
            rec.is_printed = any(rec.letter_line_ids.mapped('is_selected')) and rec.state in ['done', 'billing']

    def action_print(self):
        selected_letters = self.letter_line_ids.filtered(lambda l: l.is_selected)
        for letter in selected_letters:
            letter.is_selected = False
            return letter.generate_label_pdf()
    
    # def generate_label_pdf(self):
    #     return self.env.ref('dv_account_letter_template.action_report_letter').report_action(self)
    
    @api.depends('invoice_line_ids.invoice_name', 'invoice_line_ids.document_type_id')
    def _compute_related_invoice_names(self):
        for record in self:
            if record.invoice_line_ids:
                filter_invoice_line_ids = record.invoice_line_ids.filtered(lambda l: l.document_type_id)
                invoice_names = filter_invoice_line_ids.mapped('invoice_name')
                # Filtrar valores válidos y asegurarse de que todos sean cadenas
                invoice_names = [name or '' for name in invoice_names if isinstance(name, str)]
                # Filtrar las líneas que no tienen document_type_id
                no_document_type_lines = record.invoice_line_ids.filtered(lambda l: not l.document_type_id)
                move_line_names = no_document_type_lines.mapped('move_line_name')
                move_line_names = [name or '' for name in move_line_names if isinstance(name, str)]
                record.related_invoice_names = ','.join(invoice_names)
                # Combinar los nombres de las facturas y los nombres de las letras
                combined_names = invoice_names + move_line_names
                record.related_invoice_names = ','.join(combined_names)
            else:
                record.related_invoice_names = ''