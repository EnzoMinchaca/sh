# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'
    _check_company_auto = False

    def _get_default_amls_matching_domain(self):
        self.ensure_one()

        #Añadir las compañías hijas
        current_company = self.env.company
        company_ids = current_company.reconcile_company_child_ids.ids

        # Incluir la compañía actual en los IDs si no está ya incluida
        if current_company.id not in company_ids:
            company_ids.append(current_company.id)
        
        # Forzar el contexto para incluir ambas compañías
        ctx = dict(self.env.context)
        ctx['allowed_company_ids'] = company_ids
        
        # Buscar cuentas conciliables solo en las compañías deseadas
        all_reconcilable_accounts = self.env['account.account'].with_context(ctx).search([
            ('company_id', 'in', company_ids),
            ('reconcile', '=', True),
        ])
        all_reconcilable_account_ids = all_reconcilable_accounts.ids

        # Crear el dominio considerando ambas compañías
        domain = [
            # Base domain.
            ('display_type', 'not in', ('line_section', 'line_note')),
            ('parent_state', '=', 'posted'),
            ('company_id', 'in', company_ids),  # Filtrar por ambas compañías
            # Reconciliation domain.
            ('reconciled', '=', False),
            # Domain to use the account_move_line__unreconciled_index
            ('account_id', 'in', all_reconcilable_account_ids),
            # Special domain for payments.
            '|',
            ('account_id.account_type', 'not in', ('asset_receivable', 'liability_payable')),
            ('payment_id', '=', False),
            # Special domain for statement lines.
            ('statement_line_id', '!=', self.id),
        ]
        return domain