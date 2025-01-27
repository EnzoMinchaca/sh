# -*- coding: utf-8 -*-
# Informe de reconocimiento de ingresos
import json

from odoo import models, fields, api, _
from odoo.tools.misc import format_date
from odoo.tools import get_lang
from odoo.exceptions import UserError

from datetime import timedelta
from collections import defaultdict


class IncomeLedgerCustomHandler(models.AbstractModel):  #Informe de reconocimiento de ingresos
    _name = 'account.income.ledger.report.handler'
    _description = 'Informe de reconocimiento de ingresos'
    _inherit = 'account.report.custom.handler'

    def _get_custom_display_config(self):
        return {
            'templates': {
                'AccountReportLineName': 'account_reports.GeneralLedgerLineName',
            },
        }

    def _custom_options_initializer(self, report, options, previous_options=None):
        # Remove multi-currency columns if needed
        super()._custom_options_initializer(report, options, previous_options=previous_options)
        if self.user_has_groups('base.group_multi_currency'):
            options['multi_currency'] = True
        else:
            options['columns'] = [
                column for column in options['columns']
                if column['expression_label'] != 'amount_currency'
            ]

        # Automatically unfold the report when printing it, unless some specific lines have been unfolded
        options['unfold_all'] = (options['export_mode'] == 'print' and not options.get('unfolded_lines')) or options['unfold_all']

    def _dynamic_lines_generator(self, report, options, all_column_groups_expression_totals, warnings=None):
        lines = []
        date_from = fields.Date.from_string(options['date']['date_from'])
        company_currency = self.env.company.currency_id

        totals_by_column_group = defaultdict(lambda: {'debit': 0, 'credit': 0, 'balance': 0, 'balance_usd': 0})
        for account, column_group_results in self._query_values(report, options):
            eval_dict = {}
            has_lines = False
            for column_group_key, results in column_group_results.items():
                account_sum = results.get('sum', {})
                account_un_earn = results.get('unaffected_earnings', {})

                account_debit = account_sum.get('debit', 0.0) + account_un_earn.get('debit', 0.0)
                account_credit = account_sum.get('credit', 0.0) + account_un_earn.get('credit', 0.0)
                account_balance = account_sum.get('balance', 0.0) + account_un_earn.get('balance', 0.0)
                account_balance_usd = account_sum.get('balance_usd', 0.0) + account_un_earn.get('balance_usd', 0.0)

                eval_dict[column_group_key] = {
                    'amount_currency': account_sum.get('amount_currency', 0.0) + account_un_earn.get('amount_currency', 0.0),
                    'debit': account_debit,
                    'credit': account_credit,
                    'balance': account_balance,
                    'balance_usd': account_balance_usd,
                }

                max_date = account_sum.get('max_date')
                has_lines = has_lines or (max_date and max_date >= date_from)

                totals_by_column_group[column_group_key]['debit'] += account_debit
                totals_by_column_group[column_group_key]['credit'] += account_credit
                totals_by_column_group[column_group_key]['balance'] += account_balance
                totals_by_column_group[column_group_key]['balance_usd'] += account_balance_usd

            lines.append(self._get_account_title_line(report, options, account, has_lines, eval_dict))

        # Report total line.
        for totals in totals_by_column_group.values():
            totals['balance'] = company_currency.round(totals['balance'])
            totals['balance_usd'] = company_currency.round(totals['balance_usd'])

        # Tax Declaration lines.
        journal_options = report._get_options_journals(options)
        if len(options['column_groups']) == 1 and len(journal_options) == 1 and journal_options[0]['type'] in ('sale', 'purchase'):
            lines += self._tax_declaration_lines(report, options, journal_options[0]['type'])

        # Total line
        lines.append(self._get_total_line(report, options, totals_by_column_group))

        usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        for line in lines:
            for column in line.get('columns', []):
                if column.get('expression_label') == 'balance_usd':
                    column['currency_symbol'] = '$'
                    column['name'] = report.format_value(
                        options,
                        column['no_format'],
                        currency=usd_currency,
                        blank_if_zero=column.get('blank_if_zero', False),
                        figure_type=column.get('figure_type', 'monetary'),
                        digits=column.get('digits', 1),
                    )

        # Filtro para no mostrar las cuentas con balace total 0
        filtered_lines = [line for line in lines if not any(col.get('expression_label') == 'balance' and col.get('no_format') == 0 for col in line.get('columns', []))]

        return [(0, line) for line in filtered_lines]

    def _custom_unfold_all_batch_data_generator(self, report, options, lines_to_expand_by_function):
        account_ids_to_expand = []
        for line_dict in lines_to_expand_by_function.get('_report_expand_unfoldable_line_general_ledger', []):
            model, model_id = report._get_model_info_from_id(line_dict['id'])
            if model == 'account.account':
                account_ids_to_expand.append(model_id)

        limit_to_load = report.load_more_limit if report.load_more_limit and not options.get('export_mode') else None
        has_more_per_account_id = {}

        unlimited_aml_results_per_account_id = self._get_aml_values(report, options, account_ids_to_expand)[0]
        if limit_to_load:
            # Apply the load_more_limit.
            # load_more_limit cannot be passed to the call to _get_aml_values, otherwise it won't be applied per account but on the whole result.
            # We gain perf from batching, but load every result ; then we need to filter them.

            aml_results_per_account_id = {}
            for account_id, account_aml_results in unlimited_aml_results_per_account_id.items():
                account_values = {}
                for key, value in account_aml_results.items():
                    if len(account_values) == limit_to_load:
                        has_more_per_account_id[account_id] = True
                        break
                    account_values[key] = value
                aml_results_per_account_id[account_id] = account_values
        else:
            aml_results_per_account_id = unlimited_aml_results_per_account_id

        return {
            'initial_balances': self._get_initial_balance_values(report, account_ids_to_expand, options),
            'aml_results': aml_results_per_account_id,
            'has_more': has_more_per_account_id,
        }

    def _tax_declaration_lines(self, report, options, tax_type):
        labels_replacement = {
            'debit': _("Base Amount"),
            'credit': _("Tax Amount"),
        }

        rslt = [{
            'id': report._get_generic_line_id(None, None, markup='tax_decl_header_1'),
            'name': _('Tax Declaration'),
            'columns': [{} for column in options['columns']],
            'level': 1,
            'unfoldable': False,
            'unfolded': False,
        }, {
            'id': report._get_generic_line_id(None, None, markup='tax_decl_header_2'),
            'name': _('Name'),
            'columns': [{'name': labels_replacement.get(col['expression_label'], '')} for col in options['columns']],
            'level': 3,
            'unfoldable': False,
            'unfolded': False,
        }]

        # Call the generic tax report
        generic_tax_report = self.env.ref('account.generic_tax_report')
        tax_report_options = generic_tax_report.get_options({**options, 'selected_variant_id': generic_tax_report.id, 'forced_domain': [('tax_line_id.type_tax_use', '=', tax_type)]})
        tax_report_lines = generic_tax_report._get_lines(tax_report_options)
        tax_type_parent_line_id = generic_tax_report._get_generic_line_id(None, None, markup=tax_type)

        for tax_report_line in tax_report_lines:
            if tax_report_line.get('parent_id') == tax_type_parent_line_id:
                original_columns = tax_report_line['columns']
                row_column_map = {
                    'debit': original_columns[0],
                    'credit': original_columns[1],
                }

                tax_report_line['columns'] = [row_column_map.get(col['expression_label'], {}) for col in options['columns']]
                rslt.append(tax_report_line)

        return rslt

    def _query_values(self, report, options):
        """ Executes the queries, and performs all the computations.

        :return:    [(record, values_by_column_group), ...],  where
                    - record is an account.account record.
                    - values_by_column_group is a dict in the form {column_group_key: values, ...}
                        - column_group_key is a string identifying a column group, as in options['column_groups']
                        - values is a list of dictionaries, one per period containing:
                            - sum:                              {'debit': float, 'credit': float, 'balance': float}
                            - (optional) initial_balance:       {'debit': float, 'credit': float, 'balance': float}
                            - (optional) unaffected_earnings:   {'debit': float, 'credit': float, 'balance': float}
        """
        # Execute the queries and dispatch the results.
        query, params = self._get_query_sums(report, options)

        if not query:
            return []

        groupby_accounts = {}
        groupby_companies = {}

        self._cr.execute(query, params)
        for res in self._cr.dictfetchall():
            # No result to aggregate.
            if res['groupby'] is None:
                continue

            column_group_key = res['column_group_key']
            key = res['key']
            if key == 'sum':
                groupby_accounts.setdefault(res['groupby'], {col_group_key: {} for col_group_key in options['column_groups']})
                groupby_accounts[res['groupby']][column_group_key][key] = res

            elif key == 'initial_balance':
                groupby_accounts.setdefault(res['groupby'], {col_group_key: {} for col_group_key in options['column_groups']})
                groupby_accounts[res['groupby']][column_group_key][key] = res

            elif key == 'unaffected_earnings':
                groupby_companies.setdefault(res['groupby'], {col_group_key: {} for col_group_key in options['column_groups']})
                groupby_companies[res['groupby']][column_group_key] = res

        # Affect the unaffected earnings to the first fetched account of type 'account.data_unaffected_earnings'.
        # There is an unaffected earnings for each company but it's less costly to fetch all candidate accounts in
        # a single search and then iterate it.
        if groupby_companies:
            candidates_account_ids = self.env['account.account']._name_search(options.get('filter_search_bar'), [
                *self.env['account.account']._check_company_domain(list(groupby_companies.keys())),
                ('account_type', '=', 'equity_unaffected'),
            ])
            for account in self.env['account.account'].browse(candidates_account_ids):
                company_unaffected_earnings = groupby_companies.get(account.company_id.id)
                if not company_unaffected_earnings:
                    continue
                for column_group_key in options['column_groups']:
                    unaffected_earnings = company_unaffected_earnings[column_group_key]
                    groupby_accounts.setdefault(account.id, {col_group_key: {} for col_group_key in options['column_groups']})
                    groupby_accounts[account.id][column_group_key]['unaffected_earnings'] = unaffected_earnings
                del groupby_companies[account.company_id.id]

        # Retrieve the accounts to browse.
        # groupby_accounts.keys() contains all account ids affected by:
        # - the amls in the current period.
        # - the amls affecting the initial balance.
        # - the unaffected earnings allocation.
        # Note a search is done instead of a browse to preserve the table ordering.
        if groupby_accounts:
            accounts = self.env['account.account'].search([('id', 'in', list(groupby_accounts.keys()))])
        else:
            accounts = []
        specific_codes = [
            '48501001'
        ]
        accounts = [account for account in accounts if account.code in specific_codes]
        # Filter by date range
        if 'date' in options:
            start_date = options['date']['date_from']
            end_date = options['date']['date_to']
            accounts_ids = [account.id for account in accounts]
            filtered_move_lines = self.env['account.move.line'].search([
                ('account_id', 'in', accounts_ids),
                ('date', '>=', start_date),
                ('date', '<=', end_date),
            ])
            filtered_account_ids = filtered_move_lines.mapped('account_id.id')
            accounts = [account for account in accounts if account.id in filtered_account_ids]
            
        return [(account, groupby_accounts[account.id]) for account in accounts]

    def _get_query_sums(self, report, options):
        """ Construct a query retrieving all the aggregated sums to build the report. It includes:
        - sums for all accounts.
        - sums for the initial balances.
        - sums for the unaffected earnings.
        - sums for the tax declaration.
        :return:                    (query, params)
        """
        options_by_column_group = report._split_options_per_column_group(options)

        params = []
        queries = []

        # Create the currency table.
        # As the currency table is the same whatever the comparisons, create it only once.
        ct_query = report._get_query_currency_table(options)

        # ============================================
        # 1) Get sums for all accounts.
        # ============================================
        for column_group_key, options_group in options_by_column_group.items():
            if not options.get('general_ledger_strict_range'):
                options_group = self._get_options_sum_balance(options_group)

            # Sum is computed including the initial balance of the accounts configured to do so, unless a special option key is used
            # (this is required for trial balance, which is based on general ledger)
            sum_date_scope = 'strict_range' if options_group.get('general_ledger_strict_range') else 'normal'

            query_domain = []

            if options.get('export_mode') == 'print' and options.get('filter_search_bar'):
                query_domain.append(('account_id', 'ilike', options['filter_search_bar']))

            if options_group.get('include_current_year_in_unaff_earnings'):
                query_domain += [('account_id.include_initial_balance', '=', True)]

            tables, where_clause, where_params = report._query_get(options_group, sum_date_scope, domain=query_domain)
            params.append(column_group_key)
            params += where_params
            queries.append(f"""
                SELECT
                    account_move_line.account_id                            AS groupby,
                    'sum'                                                   AS key,
                    MAX(account_move_line.date)                             AS max_date,
                    %s                                                      AS column_group_key,
                    COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                    SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                    SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                    SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                    SUM(ROUND(account_move_line.balance_usd, currency_table.precision)) AS balance_usd
                FROM {tables}
                LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
                WHERE {where_clause}
                AND account_move_line.td_po IS NOT NULL
                AND account_move_line.td_po != ''
                GROUP BY account_move_line.account_id
            """)

            # ============================================
            # 2) Get sums for the unaffected earnings.
            # ============================================
            if not options_group.get('general_ledger_strict_range'):
                unaff_earnings_domain = [('account_id.include_initial_balance', '=', False)]

                # The period domain is expressed as:
                # [
                #   ('date' <= fiscalyear['date_from'] - 1),
                #   ('account_id.include_initial_balance', '=', False),
                # ]

                new_options = self._get_options_unaffected_earnings(options_group)
                tables, where_clause, where_params = report._query_get(new_options, 'strict_range', domain=unaff_earnings_domain)
                params.append(column_group_key)
                params += where_params
                queries.append(f"""
                    SELECT
                        account_move_line.company_id                            AS groupby,
                        'unaffected_earnings'                                   AS key,
                        NULL                                                    AS max_date,
                        %s                                                      AS column_group_key,
                        COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                        SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                        SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                        SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                        SUM(ROUND(account_move_line.balance_usd, currency_table.precision)) AS balance_usd
                    FROM {tables}
                    LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
                    WHERE {where_clause}
                    AND account_move_line.td_po IS NOT NULL
                    AND account_move_line.td_po != ''
                    GROUP BY account_move_line.company_id
                """)

        return ' UNION ALL '.join(queries), params

    def _get_options_unaffected_earnings(self, options):
        ''' Create options used to compute the unaffected earnings.
        The unaffected earnings are the amount of benefits/loss that have not been allocated to
        another account in the previous fiscal years.
        The resulting dates domain will be:
        [
          ('date' <= fiscalyear['date_from'] - 1),
          ('account_id.include_initial_balance', '=', False),
        ]
        :param options: The report options.
        :return:        A copy of the options.
        '''
        new_options = options.copy()
        new_options.pop('filter_search_bar', None)
        fiscalyear_dates = self.env.company.compute_fiscalyear_dates(fields.Date.from_string(options['date']['date_from']))

        # Trial balance uses the options key, general ledger does not
        new_date_to = fields.Date.from_string(new_options['date']['date_to']) if options.get('include_current_year_in_unaff_earnings') else fiscalyear_dates['date_from'] - timedelta(days=1)

        new_options['date'] = {
            'mode': 'single',
            'date_to': fields.Date.to_string(new_date_to),
        }

        return new_options

    def _get_aml_values(self, report, options, expanded_account_ids, offset=0, limit=None):
        rslt = {account_id: {} for account_id in expanded_account_ids}
        aml_query, aml_params = self._get_query_amls(report, options, expanded_account_ids, offset=offset, limit=limit)
        self._cr.execute(aml_query, aml_params)
        aml_results_number = 0
        has_more = False
        for aml_result in self._cr.dictfetchall():
            aml_results_number += 1
            if aml_results_number == limit:
                has_more = True
                break

            if aml_result['ref']:
                aml_result['communication'] = f"{aml_result['ref']} - {aml_result['name']}"
            else:
                aml_result['communication'] = aml_result['name']

            # The same aml can return multiple results when using account_report_cash_basis module, if the receivable/payable
            # is reconciled with multiple payments. In this case, the date shown for the move lines actually corresponds to the
            # reconciliation date. In order to keep distinct lines in this case, we include date in the grouping key.
            aml_key = (aml_result['id'], aml_result['date'])

            account_result = rslt[aml_result['account_id']]
            if not aml_key in account_result:
                account_result[aml_key] = {col_group_key: {} for col_group_key in options['column_groups']}

            already_present_result = account_result[aml_key][aml_result['column_group_key']]
            if already_present_result:
                # In case the same move line gives multiple results at the same date, add them.
                # This does not happen in standard GL report, but could because of custom shadowing of account.move.line,
                # such as the one done in account_report_cash_basis (if the payable/receivable line is reconciled twice at the same date).
                already_present_result['debit'] += aml_result['debit']
                already_present_result['credit'] += aml_result['credit']
                already_present_result['balance'] += aml_result['balance']
                already_present_result['amount_currency'] += aml_result['amount_currency']
            else:
                account_result[aml_key][aml_result['column_group_key']] = aml_result

        return rslt, has_more

    def _get_query_amls(self, report, options, expanded_account_ids, offset=0, limit=None):
        """ Construct a query retrieving the account.move.lines when expanding a report line with or without the load
        more.
        :param options:               The report options.
        :param expanded_account_ids:  The account.account ids corresponding to consider. If None, match every account.
        :param offset:                The offset of the query (used by the load more).
        :param limit:                 The limit of the query (used by the load more).
        :return:                      (query, params)
        """
        additional_domain = [('account_id', 'in', expanded_account_ids)] if expanded_account_ids is not None else None
        queries = []
        all_params = []
        lang = self.env.user.lang or get_lang(self.env).code
        journal_name = f"COALESCE(journal.name->>'{lang}', journal.name->>'en_US')" if \
            self.pool['account.journal'].name.translate else 'journal.name'
        account_name = f"COALESCE(account.name->>'{lang}', account.name->>'en_US')" if \
            self.pool['account.account'].name.translate else 'account.name'
        for column_group_key, group_options in report._split_options_per_column_group(options).items():
            # Get sums for the account move lines.
            # period: [('date' <= options['date_to']), ('date', '>=', options['date_from'])]
            tables, where_clause, where_params = report._query_get(group_options, domain=additional_domain, date_scope='strict_range')
            ct_query = report._get_query_currency_table(group_options)
            query = f'''
                (SELECT
                    account_move_line.id,
                    account_move_line.date,
                    account_move_line.date_maturity,
                    account_move_line.name,
                    account_move_line.ref,
                    account_move_line.company_id,
                    account_move_line.account_id,
                    account_move_line.payment_id,
                    account_move_line.partner_id,
                    account_move_line.currency_id,
                    account_move_line.amount_currency,
                    COALESCE(account_move_line.invoice_date, account_move_line.date)                 AS invoice_date,
                    ROUND(account_move_line.debit * currency_table.rate, currency_table.precision)   AS debit,
                    ROUND(account_move_line.credit * currency_table.rate, currency_table.precision)  AS credit,
                    ROUND(account_move_line.balance * currency_table.rate, currency_table.precision) AS balance,
                    ROUND(account_move_line.balance_usd, currency_table.precision) AS balance_usd,
                    account_move_line.td_po                 AS td_po,
                    account_move_line.td_invoice            AS td_invoice,
                    account_move_line.td_partner_ref        AS td_partner_ref,
                    move.name                               AS move_name,
                    company.currency_id                     AS company_currency_id,
                    partner.name                            AS partner_name,
                    move.move_type                          AS move_type,
                    account.code                            AS account_code,
                    {account_name}                          AS account_name,
                    journal.code                            AS journal_code,
                    {journal_name}                          AS journal_name,
                    full_rec.id                             AS full_rec_name,
                    %s                                      AS column_group_key
                FROM {tables}
                JOIN account_move move                      ON move.id = account_move_line.move_id
                LEFT JOIN {ct_query}                        ON currency_table.company_id = account_move_line.company_id
                LEFT JOIN res_company company               ON company.id = account_move_line.company_id
                LEFT JOIN res_partner partner               ON partner.id = account_move_line.partner_id
                LEFT JOIN account_account account           ON account.id = account_move_line.account_id
                LEFT JOIN account_journal journal           ON journal.id = account_move_line.journal_id
                LEFT JOIN account_full_reconcile full_rec   ON full_rec.id = account_move_line.full_reconcile_id
                WHERE {where_clause}
                AND account_move_line.td_po IS NOT NULL
                AND account_move_line.td_po != ''
                ORDER BY account_move_line.date, account_move_line.id)
            '''

            queries.append(query)
            all_params.append(column_group_key)
            all_params += where_params

        full_query = " UNION ALL ".join(queries)

        if offset:
            full_query += ' OFFSET %s '
            all_params.append(offset)
        if limit:
            full_query += ' LIMIT %s '
            all_params.append(limit)

        return (full_query, all_params)

    def _get_initial_balance_values(self, report, account_ids, options):
        """
        Get sums for the initial balance.
        """
        queries = []
        params = []
        for column_group_key, options_group in report._split_options_per_column_group(options).items():
            new_options = self._get_options_initial_balance(options_group)
            ct_query = report._get_query_currency_table(new_options)
            domain = [('account_id', 'in', account_ids)]
            if new_options.get('include_current_year_in_unaff_earnings'):
                domain += [('account_id.include_initial_balance', '=', True)]
            tables, where_clause, where_params = report._query_get(new_options, 'normal', domain=domain)
            params.append(column_group_key)
            params += where_params
            queries.append(f"""
                SELECT
                    account_move_line.account_id                                                          AS groupby,
                    'initial_balance'                                                                     AS key,
                    NULL                                                                                  AS max_date,
                    %s                                                                                    AS column_group_key,
                    COALESCE(SUM(account_move_line.amount_currency), 0.0)                                 AS amount_currency,
                    SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                    SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                    SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance
                FROM {tables}
                LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
                WHERE {where_clause}
                AND account_move_line.td_po IS NOT NULL
                AND account_move_line.td_po != ''
                GROUP BY account_move_line.account_id
            """)

        self._cr.execute(" UNION ALL ".join(queries), params)

        init_balance_by_col_group = {
            account_id: {column_group_key: {} for column_group_key in options['column_groups']}
            for account_id in account_ids
        }
        for result in self._cr.dictfetchall():
            init_balance_by_col_group[result['groupby']][result['column_group_key']] = result

        accounts = self.env['account.account'].browse(account_ids)
        return {
            account.id: (account, init_balance_by_col_group[account.id])
            for account in accounts
        }

    def _get_options_initial_balance(self, options):
        """ Create options used to compute the initial balances.
        The initial balances depict the current balance of the accounts at the beginning of
        the selected period in the report.
        The resulting dates domain will be:
        [
            ('date' <= options['date_from'] - 1),
            '|',
            ('date' >= fiscalyear['date_from']),
            ('account_id.include_initial_balance', '=', True)
        ]
        :param options: The report options.
        :return:        A copy of the options.
        """
        #pylint: disable=sql-injection
        new_options = options.copy()
        date_to = new_options['comparison']['periods'][-1]['date_from'] if new_options.get('comparison', {}).get('periods') else new_options['date']['date_from']
        new_date_to = fields.Date.from_string(date_to) - timedelta(days=1)

        # Date from computation
        # We have two case:
        # 1) We are choosing a date that starts at the beginning of a fiscal year and we want the initial period to be
        # the previous fiscal year
        # 2) We are choosing a date that starts in the middle of a fiscal year and in that case we want the initial period
        # to be the beginning of the fiscal year
        date_from = fields.Date.from_string(new_options['date']['date_from'])
        current_fiscalyear_dates = self.env.company.compute_fiscalyear_dates(date_from)

        if date_from == current_fiscalyear_dates['date_from']:
            # We want the previous fiscal year
            previous_fiscalyear_dates = self.env.company.compute_fiscalyear_dates(date_from - timedelta(days=1))
            new_date_from = previous_fiscalyear_dates['date_from']
            include_current_year_in_unaff_earnings = True
        else:
            # We want the current fiscal year
            new_date_from = current_fiscalyear_dates['date_from']
            include_current_year_in_unaff_earnings = False

        new_options['date'] = {
            'mode': 'range',
            'date_from': fields.Date.to_string(new_date_from),
            'date_to': fields.Date.to_string(new_date_to),
        }
        new_options['include_current_year_in_unaff_earnings'] = include_current_year_in_unaff_earnings

        return new_options

    def _get_options_sum_balance(self, options):
        new_options = options.copy()

        if not options.get('general_ledger_strict_range'):
            # Date from
            date_from = fields.Date.from_string(new_options['date']['date_from'])
            current_fiscalyear_dates = self.env.company.compute_fiscalyear_dates(date_from)
            new_date_from = current_fiscalyear_dates['date_from']

            new_date_to = new_options['date']['date_to']

            new_options['date'] = {
                'mode': 'range',
                'date_from': fields.Date.to_string(new_date_from),
                'date_to': new_date_to,
            }

        return new_options

    ####################################################
    # COLUMN/LINE HELPERS
    ####################################################
    def _get_account_title_line(self, report, options, account, has_lines, eval_dict):
        line_columns = []
        for column in options['columns']:
            col_value = eval_dict[column['column_group_key']].get(column['expression_label'])
            col_expr_label = column['expression_label']

            value = None if col_value is None or (col_expr_label == 'amount_currency' and not account.currency_id) else col_value

            line_columns.append(report._build_column_dict(
                value,
                column,
                options=options,
                currency=account.currency_id if col_expr_label == 'amount_currency' else None,
            ))

        line_id = report._get_generic_line_id('account.account', account.id)
        is_in_unfolded_lines = any(
            report._get_res_id_from_line_id(line_id, 'account.account') == account.id
            for line_id in options.get('unfolded_lines')
        )
        return {
            'id': line_id,
            'name': f'{account.code} {account.name}',
            'columns': line_columns,
            'level': 1,
            'unfoldable': has_lines,
            'unfolded': has_lines and (is_in_unfolded_lines or options.get('unfold_all')),
            'expand_function': '_report_expand_unfoldable_line_general_ledger',
        }

    def _get_aml_line(self, report, parent_line_id, options, eval_dict, init_bal_by_col_group):
        line_columns = []
        usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)  # Buscar la moneda USD

        for column in options['columns']:
            col_expr_label = column['expression_label']
            col_value = eval_dict[column['column_group_key']].get(col_expr_label)
            col_currency = None

            if col_value is not None:
                if col_expr_label == 'amount_currency':
                    col_currency = self.env['res.currency'].browse(eval_dict[column['column_group_key']]['currency_id'])
                    col_value = None if col_currency == self.env.company.currency_id else col_value
                elif col_expr_label == 'balance_usd':
                    # Aquí estableces el símbolo de dólar como moneda
                    col_currency = self.env['res.currency'].search([('symbol', '=', '$')], limit=1)
                # elif col_expr_label == 'balance':
                #     col_value += (init_bal_by_col_group[column['column_group_key']] or 0)

            # line_columns.append(report._build_column_dict(
            #     col_value,
            #     column,
            #     options=options,
            #     currency=col_currency,
            # ))

            column_dict = report._build_column_dict(
                col_value,
                column,
                options=options,
                currency=col_currency,
            )

            # Modificamos el símbolo de moneda para 'balance_usd'
            if col_expr_label == 'balance_usd':
                column_dict['currency_symbol'] = '$'
                column_dict['currency'] = usd_currency.id

            line_columns.append(column_dict)

        aml_id = None
        move_name = None
        caret_type = None
        for column_group_dict in eval_dict.values():
            aml_id = column_group_dict.get('id', '')
            if aml_id:
                if column_group_dict.get('payment_id'):
                    caret_type = 'account.payment'
                else:
                    caret_type = 'account.move.line'
                move_name = column_group_dict['move_name']
                date = str(column_group_dict.get('date', ''))
                break

        return {
            'id': report._get_generic_line_id('account.move.line', aml_id, parent_line_id=parent_line_id, markup=date),
            'caret_options': caret_type,
            'parent_id': parent_line_id,
            'name': move_name,
            'columns': line_columns,
            'level': 3,
        }

    @api.model
    def _get_total_line(self, report, options, eval_dict):
        line_columns = []
        for column in options['columns']:
            col_value = eval_dict[column['column_group_key']].get(column['expression_label'])
            col_value = None if col_value is None else col_value

            line_columns.append(report._build_column_dict(col_value, column, options=options))

        return {
            'id': report._get_generic_line_id(None, None, markup='total'),
            'name': _('Total'),
            'level': 1,
            'columns': line_columns,
        }

    def caret_option_audit_tax(self, options, params):
        return self.env['account.generic.tax.report.handler'].caret_option_audit_tax(options, params)

    def _report_expand_unfoldable_line_general_ledger(self, line_dict_id, groupby, options, progress, offset, unfold_all_batch_data=None):
        def init_load_more_progress(line_dict):
            return {
                column['column_group_key']: line_col.get('no_format', 0)
                for column, line_col in  zip(options['columns'], line_dict['columns'])
                if column['expression_label'] == 'balance'
            }

        report = self.env.ref('account_reports.general_ledger_report')
        model, model_id = report._get_model_info_from_id(line_dict_id)

        if model != 'account.account':
            raise UserError(_("Wrong ID for general ledger line to expand: %s", line_dict_id))

        lines = []

        # Get initial balance
        # if offset == 0:
        #     if unfold_all_batch_data:
        #         account, init_balance_by_col_group = unfold_all_batch_data['initial_balances'][model_id]
        #     else:
        #         account, init_balance_by_col_group = self._get_initial_balance_values(report, [model_id], options)[model_id]

        #     initial_balance_line = report._get_partner_and_general_ledger_initial_balance_line(options, line_dict_id, init_balance_by_col_group, account.currency_id)

        #     if initial_balance_line:
        #         lines.append(initial_balance_line)

        #         # For the first expansion of the line, the initial balance line gives the progress
        #         progress = init_load_more_progress(initial_balance_line)

        # Get move lines
        limit_to_load = report.load_more_limit + 1 if report.load_more_limit and options['export_mode'] != 'print' else None
        if unfold_all_batch_data:
            aml_results = unfold_all_batch_data['aml_results'][model_id]
            has_more = unfold_all_batch_data['has_more'].get(model_id, False)
        else:
            aml_results, has_more = self._get_aml_values(report, options, [model_id], offset=offset, limit=limit_to_load)
            aml_results = aml_results[model_id]

        next_progress = progress
        for aml_result in aml_results.values():
            new_line = self._get_aml_line(report, line_dict_id, options, aml_result, next_progress)
            lines.append(new_line)
            next_progress = init_load_more_progress(new_line)

        # Generar líneas de nivel 2
        level_2_lines = self._generate_level_2_lines(aml_results, report, line_dict_id, new_line['columns'], options)

        # Ordenar ambas listas de líneas
        # Las líneas de nivel 2 tienen el valor de td_po directamente en 'td_po', mientras que las de nivel 3 están en 'columns'
        combined_lines = sorted(
            level_2_lines + lines, 
            key=lambda l: self._get_td_po_from_columns_or_level_2(l)
        )

        # Identificar los 'td_po' que deben eliminarse
        td_po_to_remove = set()
        
        # Recorre las líneas de nivel 2 para verificar los valores de 'balance' y 'balance_usd'
        for line in level_2_lines:
            if line.get('level') == 2:
                columns = line.get('columns', [])
                balance = next((col.get('no_format', 0) for col in columns if col.get('expression_label') == 'balance'), 0)
                balance_usd = next((col.get('no_format', 0) for col in columns if col.get('expression_label') == 'balance_usd'), 0)
                
                # Si balance o balance_usd es 0, marcar 'td_po' para eliminación
                if balance == 0 and balance_usd == 0:
                    td_po_to_remove.add(self._get_td_po_from_columns_or_level_2(line))
        
        # Filtrar las líneas eliminando las que tengan 'td_po' en la lista de eliminación
        final_lines = []
        last_level_2_id = None
        for line in combined_lines:
            if line.get('level') == 2:
                td_po = line.get('td_po', '')
                if td_po in td_po_to_remove:
                    continue  # No agregar la línea de nivel 2 si debe ser eliminada
            
            # Para las líneas de nivel 3, verificar si su 'td_po' debe ser eliminado
            if line.get('level') == 3:
                columns = line.get('columns', [])
                td_po = self._get_td_po_from_columns(columns)
                if td_po in td_po_to_remove:
                    continue  # No agregar la línea de nivel 3 si su 'td_po' debe ser eliminado
            
            final_lines.append(line)

        return {
            'lines': final_lines,
            'offset_increment': report.load_more_limit,
            'has_more': has_more,
            'progress': next_progress,
        }
    
    def _get_td_po_from_columns_or_level_2(self, line):
        """
        Extrae el valor de 'td_po' para las líneas de nivel 2 y 3.
        Si es una línea de nivel 2, utiliza el campo 'td_po' directamente.
        Si es una línea de nivel 3, lo busca dentro de las columnas.
        """
        # Si es nivel 2, el td_po está en la propia línea
        if line.get('level') == 2:
            return line.get('td_po', '')

        # Si es nivel 3, el td_po está en las columnas
        return self._get_td_po_from_columns(line.get('columns', []))
    
    def _get_td_po_from_columns(self, columns):
        """
        Extrae el valor de 'td_po' desde las columnas si está presente.
        """
        for col in columns:
            if col.get('expression_label') == 'td_po':
                return col.get('no_format', col.get('name', ''))  # Devuelve el valor formateado o el original si existe
        return ''

    def _generate_level_2_lines(self, aml_results, report, parent_line_id, columns, options):
        grouped_lines = {}
        level_2_lines = []

        usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        currency_id = self.env.company.currency_id

        # Iterar sobre los resultados para agrupar por td_po
        for aml_key, aml_data in aml_results.items():
            # Desanidar la clave del diccionario si es necesario
            for key, value in aml_data.items():
                if isinstance(value, dict):
                    td_po = value.get('td_po')
                    balance = value.get('balance', 0)
                    balance_usd = value.get('balance_usd', 0)
                    
                    if td_po:
                        break
            else:
                # Si no encontramos td_po en los datos, continuamos al siguiente resultado
                continue
            
            if td_po not in grouped_lines:
                grouped_lines[td_po] = {
                    'total_debit': 0,
                    'total_credit': 0,
                    'total_balance': 0,
                    'total_balance_usd': 0,
                    'td_po': td_po
                }

            # Sumar valores, asegurando que las claves existan en aml_data
            grouped_lines[td_po]['total_debit'] += value.get('debit', 0)
            grouped_lines[td_po]['total_credit'] += value.get('credit', 0)
            grouped_lines[td_po]['total_balance'] += balance
            grouped_lines[td_po]['total_balance_usd'] += balance_usd

        # Crear líneas de nivel 2
        for td_po, group_data in grouped_lines.items():
            
            level_2_line = {
                'id': report._get_generic_line_id('account.move.line', f"{td_po}_{aml_key}", parent_line_id=parent_line_id, markup=td_po),
                'name': f'PO {td_po}',
                'columns': [],
                'level': 2,
                'td_po': td_po
            }
            
            # Generar columnas manteniendo el formato original
            for col in columns:
                column_copy = col.copy()  # Crear una copia de la columna original para mantener el formato

                if col['expression_label'] == 'balance':
                    column_copy['no_format'] = group_data['total_balance']
                    balance_value = report.format_value(
                        options, 
                        group_data['total_balance'], 
                        currency=currency_id, 
                        blank_if_zero=column_copy.get('blank_if_zero', False),
                        figure_type=column_copy.get('figure_type', 'monetary'),
                        digits=column_copy.get('digits', 1),
                    )
                    column_copy['name'] = balance_value[0] if isinstance(balance_value, tuple) else balance_value
                elif col['expression_label'] == 'balance_usd':
                    column_copy['no_format'] = group_data['total_balance_usd']
                    balance_usd_value = report.format_value(
                        options, 
                        group_data['total_balance_usd'], 
                        currency=usd_currency, 
                        blank_if_zero=column_copy.get('blank_if_zero', False),
                        figure_type=column_copy.get('figure_type', 'monetary'),
                        digits=column_copy.get('digits', 1),
                    )
                    column_copy['name'] = balance_usd_value[0] if isinstance(balance_usd_value, tuple) else balance_usd_value

                # Agregar la columna formateada a la línea de nivel 2
                level_2_line['columns'].append(column_copy)

            level_2_lines.append(level_2_line)

        return level_2_lines
    