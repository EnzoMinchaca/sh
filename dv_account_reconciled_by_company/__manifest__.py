# -*- coding: utf-8 -*-
{
    'name': "Conciliación de cuentas multicompañia",

    'summary': """
        Módulo dedicado a la conciliación de cuentas multicompañia.""",

    'author': 'Develogers',
	'website': "https://develogers.com/",
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'Other proprietary',

    'category': 'Accounting/Accounting',
    'version': '17.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account_accountant'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/dv_account_reconciled_by_company_security.xml',
        'views/res_company_views.xml',
        'views/bank_rec_widget_views.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'dv_account_reconciled_by_company/static/src/js/embedded_list_view.js',
        ],
    },

    'images': ['static/description/banner.gif'],
    'application': True,
    'installable': True,
    'auto_install': False,
}

