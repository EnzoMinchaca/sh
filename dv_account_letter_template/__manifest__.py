# -*- coding: utf-8 -*-
{
    'name': "Formato físico de canje de Letras",

    'summary': """
        Módulo para obtener el formato físico del reporte de letras.""",

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
    ],

    'data': [
        'views/account_letter_views.xml',
        'views/account_letter_line_views.xml',
        'views/report.xml',
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dv_account_letter_template/static/src/scss/custom_styles.scss',
        ],
    },
    'images': ['static/description/banner.gif'],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

