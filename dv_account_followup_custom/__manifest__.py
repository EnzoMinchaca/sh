# -*- coding: utf-8 -*-
{
    'name': "Reporte Personalizado de Seguimiento de Deuda",

    'summary': """
        Módulo que personaliza el reporte de seguimiento de deuda de clientes generándolo en PDF y excel.""",

    'author': 'Develogers',
	'website': "https://develogers.com/",
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'Other proprietary',

    'category': 'Accounting/Accounting',
    'version': '17.1',

    'depends': [
        'base', 
        'dv_account_letter',
        'account',
        'account_followup',
        'account_edi'
    ],

    'data': [
        'views/report.xml',
        'views/template_report.xml',
        'views/account_followup_views.xml',
    ],

    'images': ['static/description/icon.png'],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

