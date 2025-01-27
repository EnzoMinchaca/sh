# -*- coding: utf-8 -*-
{
    'name': "Reportes de contabilidad en moneda",

    'summary': """
        Módulo para generar los informes de contabilidad en moneda.""",

    'author': "Develogers",
    'website': "https://develogers.com/",
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'Other proprietary',

    'category': 'Accounting/Accounting',
    'version': '17.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account_reports', 'account', 'td_import_journal_entries'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/balance_sheet.xml',
        'data/profit_and_loss.xml',
        'views/account_move_line_views.xml',
    ],
    'images': ['static/description/banner.gif'],

    'application': True,
	'installable': True,
	'auto_install': False,
}

