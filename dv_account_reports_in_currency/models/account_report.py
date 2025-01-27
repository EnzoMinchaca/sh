# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _
from ast import literal_eval
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from itertools import chain
from odoo.exceptions import RedirectWarning, UserError, ValidationError
import json
import re

class AccountReport(models.Model):
    _inherit = 'account.report'

    def _compute_formula_batch_with_engine_domain(self, options, date_scope, formulas_dict, current_groupby, next_groupby, offset=0, limit=None, warnings=None):
        """ Report engine.

        Formulas made for this engine consist of a domain on account.move.line. Only those move lines will be used to compute the result.

        This engine supports a few subformulas, each returning a slighlty different result:
        - sum: the result will be sum of the matched move lines' balances

        - sum_if_pos: the result will be the same as sum only if it's positive; else, it will be 0

        - sum_if_neg: the result will be the same as sum only if it's negative; else, it will be 0

        - count_rows: the result will be the number of sublines this expression has. If the parent report line has no groupby,
                      then it will be the number of matching amls. If there is a groupby, it will be the number of distinct grouping
                      keys at the first level of this groupby (so, if groupby is 'partner_id, account_id', the number of partners).
        """
        def _format_result_depending_on_groupby(formula_rslt):
            if not current_groupby:
                if formula_rslt:
                    # There should be only one element in the list; we only return its totals (a dict) ; so that a list is only returned in case
                    # of a groupby being unfolded.
                    return formula_rslt[0][1]
                else:
                    # No result at all
                    return {
                        'sum': 0,
                        'sum_if_pos': 0,
                        'sum_if_neg': 0,
                        'count_rows': 0,
                        'has_sublines': False,
                        'balance_usd': 0,
                    }
            return formula_rslt

        self._check_groupby_fields((next_groupby.split(',') if next_groupby else []) + ([current_groupby] if current_groupby else []))

        groupby_sql = f'account_move_line.{current_groupby}' if current_groupby else None
        ct_query = self._get_query_currency_table(options)

        rslt = {}

        for formula, expressions in formulas_dict.items():
            try:
                line_domain = literal_eval(formula)
            except (ValueError, SyntaxError):
                raise UserError(_("Invalid domain formula in expression %r of line %r: %s", expressions.label, expressions.report_line_id.name, formula))
            tables, where_clause, where_params = self._query_get(options, date_scope, domain=line_domain)

            tail_query, tail_params = self._get_engine_query_tail(offset, limit)
            query = f"""
                SELECT
                    COALESCE(SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)), 0.0) AS sum,
                    COALESCE(SUM(ROUND(account_move_line.balance_usd, currency_table.precision)), 0.0) AS sum_usd,
                    COUNT(DISTINCT account_move_line.{next_groupby.split(',')[0] if next_groupby else 'id'}) AS count_rows
                    {f', {groupby_sql} AS grouping_key' if groupby_sql else ''}
                FROM {tables}
                JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
                WHERE {where_clause}
                {f' GROUP BY {groupby_sql}' if groupby_sql else ''}
                {tail_query}
            """

            # Fetch the results.
            formula_rslt = []
            self._cr.execute(query, where_params + tail_params)
            all_query_res = self._cr.dictfetchall()

            total_sum = 0
            total_sum_usd = 0
            for query_res in all_query_res:
                res_sum = query_res['sum']
                res_sum_usd = query_res['sum_usd']
                total_sum += res_sum
                total_sum_usd += res_sum_usd
                totals = {
                    'sum': res_sum,
                    'sum_usd': res_sum_usd,
                    'sum_if_pos': 0,
                    'sum_if_neg': 0,
                    'count_rows': query_res['count_rows'],
                    'has_sublines': query_res['count_rows'] > 0,
                }
                formula_rslt.append((query_res.get('grouping_key', None), totals))

            # Handle sum_if_pos, -sum_if_pos, sum_if_neg and -sum_if_neg
            expressions_by_sign_policy = defaultdict(lambda: self.env['account.report.expression'])
            for expression in expressions:
                subformula_without_sign = expression.subformula.replace('-', '').strip()
                if subformula_without_sign in ('sum_if_pos', 'sum_if_neg'):
                    expressions_by_sign_policy[subformula_without_sign] += expression
                else:
                    expressions_by_sign_policy['no_sign_check'] += expression

            # Then we have to check the total of the line and only give results if its sign matches the desired policy.
            # This is important for groupby managements, for which we can't just check the sign query_res by query_res
            if expressions_by_sign_policy['sum_if_pos'] or expressions_by_sign_policy['sum_if_neg']:
                sign_policy_with_value = 'sum_if_pos' if self.env.company.currency_id.compare_amounts(total_sum, 0.0) >= 0 else 'sum_if_neg'
                # >= instead of > is intended; usability decision: 0 is considered positive

                formula_rslt_with_sign = [(grouping_key, {**totals, sign_policy_with_value: totals['sum']}) for grouping_key, totals in formula_rslt]

                for sign_policy in ('sum_if_pos', 'sum_if_neg'):
                    policy_expressions = expressions_by_sign_policy[sign_policy]

                    if policy_expressions:
                        if sign_policy == sign_policy_with_value:
                            rslt[(formula, policy_expressions)] = _format_result_depending_on_groupby(formula_rslt_with_sign)
                        else:
                            rslt[(formula, policy_expressions)] = _format_result_depending_on_groupby([])

            if expressions_by_sign_policy['no_sign_check']:
                rslt[(formula, expressions_by_sign_policy['no_sign_check'])] = _format_result_depending_on_groupby(formula_rslt)

        return rslt
    
    def _build_static_line_columns(self, line, options, all_column_groups_expression_totals):
        usd_currency = self.env.ref('base.USD')
        line_expressions_map = {expr.label: expr for expr in line.expression_ids}
        columns = []
        for column_data in options['columns']:
            current_group_expression_totals = all_column_groups_expression_totals[column_data['column_group_key']]
            target_line_res_dict = {expr.label: current_group_expression_totals[expr] for expr in line.expression_ids if not expr.label.startswith('_default')}

            column_expr_label = column_data['expression_label']
            column_res_dict = target_line_res_dict.get(column_expr_label, {})
            column_value = column_res_dict.get('value')
            column_has_sublines = column_res_dict.get('has_sublines', False)
            column_expression = line_expressions_map.get(column_expr_label, self.env['account.report.expression'])
            figure_type = column_expression.figure_type or column_data['figure_type']

            # Handle info popup
            info_popup_data = {}

            # Check carryover
            carryover_expr_label = '_carryover_%s' % column_expr_label
            carryover_value = target_line_res_dict.get(carryover_expr_label, {}).get('value', 0)
            if self.env.company.currency_id.compare_amounts(0, carryover_value) != 0:
                info_popup_data['carryover'] = self._format_value(options, carryover_value, figure_type='monetary')

                carryover_expression = line_expressions_map[carryover_expr_label]
                if carryover_expression.carryover_target:
                    info_popup_data['carryover_target'] = carryover_expression._get_carryover_target_expression(options).display_name
                # If it's not set, it means the carryover needs to target the same expression

            applied_carryover_value = target_line_res_dict.get('_applied_carryover_%s' % column_expr_label, {}).get('value', 0)
            if self.env.company.currency_id.compare_amounts(0, applied_carryover_value) != 0:
                info_popup_data['applied_carryover'] = self._format_value(options, applied_carryover_value, figure_type='monetary')
                info_popup_data['allow_carryover_audit'] = self.user_has_groups('base.group_no_one')
                info_popup_data['expression_id'] = line_expressions_map['_applied_carryover_%s' % column_expr_label]['id']
                info_popup_data['column_group_key'] = column_data['column_group_key']

            # Handle manual edition popup
            edit_popup_data = {}
            formatter_params = {}
            if column_expression.engine == 'external' and column_expression.subformula \
                and len(options['companies']) == 1 \
                and (not options['available_vat_fiscal_positions'] or options['fiscal_position'] != 'all'):

                # Compute rounding for manual values
                rounding = None
                if figure_type == 'integer':
                    rounding = 0
                else:
                    rounding_opt_match = re.search(r"\Wrounding\W*=\W*(?P<rounding>\d+)", column_expression.subformula)
                    if rounding_opt_match:
                        rounding = int(rounding_opt_match.group('rounding'))
                    elif figure_type == 'monetary':
                        rounding = self.env.company.currency_id.decimal_places

                if 'editable' in column_expression.subformula:
                    edit_popup_data = {
                        'column_group_key': column_data['column_group_key'],
                        'target_expression_id': column_expression.id,
                        'rounding': rounding,
                        'figure_type': figure_type,
                        'column_value': column_value,
                    }

                formatter_params['digits'] = rounding

            # Build result
            if column_value is not None: #In case column value is zero, we still want to go through the condition
                foreign_currency_id = target_line_res_dict.get(f'_currency_{column_expr_label}', {}).get('value')
                if foreign_currency_id:
                    formatter_params['currency'] = self.env['res.currency'].browse(foreign_currency_id)
                if '_usd' in column_expr_label:
                    formatter_params['currency'] = usd_currency

            column_data = self._build_column_dict(
                column_value,
                column_data,
                options=options,
                column_expression=column_expression if column_expression else None,
                has_sublines=column_has_sublines,
                report_line_id=line.id,
                **formatter_params,
            )

            if info_popup_data:
                column_data['info_popup_data'] = json.dumps(info_popup_data)

            if edit_popup_data:
                column_data['edit_popup_data'] = json.dumps(edit_popup_data)

            columns.append(column_data)

        return columns