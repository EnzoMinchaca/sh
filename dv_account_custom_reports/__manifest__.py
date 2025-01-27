# -*- coding: utf-8 -*-
{
    'name': "Informes de conciliación e ingresos",

    'summary': """
        Módulo para la generación de reportes de conciliación y reconocimiento de ingresos.""",

    'author': "Develogers",
    'website': "https://develogers.com/",
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'Other proprietary',

    'category': 'Accounting/Accounting',
    'version': '17.1',

    'depends': ['base', 'account_reports', 'account', 'td_import_journal_entries'],

    'data': [
        'security/ir.model.access.csv',
        'data/reconcile_sheet_po.xml',
        'data/reconcile_sheet_invoice.xml',
        'data/income_sheet.xml',
        #'views/views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            #'dv_account_custom_reports/static/src/components/account_reports/search_bar/search_bar.js',
            'dv_account_custom_reports/static/src/components/**/*',
        ],
    },
    'images': ['static/description/banner.gif'],

    'application': True,
	'installable': True,
	'auto_install': False,
}

