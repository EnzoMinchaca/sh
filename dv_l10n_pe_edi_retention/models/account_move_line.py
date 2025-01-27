from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    l10n_pe_is_withholding_line = fields.Boolean(
        string='Es apunte de retención', copy=False, compute='_compute_l10n_pe_is_withholding_line', store=True)
    
    @api.depends('amount_currency', 'move_id.l10n_pe_is_subject_to_withholding')
    def _compute_l10n_pe_is_withholding_line(self):
        for line in self:
            if not line.move_id.l10n_pe_is_subject_to_withholding:
                line.l10n_pe_is_withholding_line = False
            else:
                if abs(line.amount_currency) == line.move_id.l10n_pe_withholding_amount and line.account_id.account_type in ['liability_payable', 'asset_receivable']:
                    line.l10n_pe_is_withholding_line = True
    
    @api.depends('product_id')
    def _compute_name(self):
        # Agrupar las líneas de términos de pago por movimiento y ordenarlas por fecha de vencimiento
        term_by_move = (self.move_id.line_ids | self).filtered(lambda l: l.display_type == 'payment_term').sorted(lambda l: l.date_maturity if l.date_maturity else date.max).grouped('move_id')
        
        for line in self.filtered(lambda l: l.move_id.inalterable_hash is False):
            # Verificar si la factura tiene retención
            has_withholding = line.move_id.l10n_pe_withholding_amount > 0
            is_posted = line.move_id.state == 'posted'

            # Aplicar nueva lógica solo si hay retención y el asiento está publicado
            if has_withholding and is_posted:
                if line.display_type == 'payment_term':
                    # Obtener las líneas de términos de pago para el movimiento actual
                    term_lines = term_by_move.get(line.move_id, self.env['account.move.line'])

                    # Separar las líneas de retención y las demás
                    withholding_lines = term_lines.filtered(lambda l: l.l10n_pe_is_withholding_line)
                    non_withholding_lines = term_lines - withholding_lines

                    # Ordenar las líneas no de retención y agregar la retención al final
                    sorted_lines = non_withholding_lines.sorted(lambda l: l.date_maturity if l.date_maturity else date.max) + withholding_lines

                    # Asignar el índice correcto a cada línea en sorted_lines
                    for index, sorted_line in enumerate(sorted_lines):
                        name = sorted_line.move_id.payment_reference or ''
                        name = _('%s cuota #%s', name, index + 1).lstrip()
                        sorted_line.name = name
            else:
                # Flujo nativo: no modificar el índice ni mostrar la cuota si es un solo apunte
                if line.display_type == 'payment_term' and len(term_by_move.get(line.move_id, [])) > 1:
                    term_lines = term_by_move.get(line.move_id, self.env['account.move.line'])
                    index = term_lines._ids.index(line.id) + 1 if line in term_lines else 1
                    name = line.move_id.payment_reference or ''
                    name = _('%s cuota #%s', name, index).lstrip()
                    line.name = name
            
            if not line.product_id or line.display_type in ('line_section', 'line_note'):
                continue
            
            if line.partner_id.lang:
                product = line.product_id.with_context(lang=line.partner_id.lang)
            else:
                product = line.product_id

            values = []
            if product.partner_ref:
                values.append(product.partner_ref)
            if line.journal_id.type == 'sale':
                if product.description_sale:
                    values.append(product.description_sale)
            elif line.journal_id.type == 'purchase':
                if product.description_purchase:
                    values.append(product.description_purchase)
            line.name = '\n'.join(values)