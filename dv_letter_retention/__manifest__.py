# -*- coding: utf-8 -*-
{
    'name': "Retención integrado al canje de Letras",

    'summary': """
        Módulo que integra la reención de facturas con el canje de letras, enlazando
        los módulos dv_l10n_pe_edi_retention con dv_account_letter.""",

    'author': 'Develogers',
	'website': "https://develogers.com/",
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'Other proprietary',

    'category': 'Accounting/Accounting',
    'version': '17.1',

    'depends': [
        'dv_account_letter',
        'dv_l10n_pe_edi_retention',
    ],

    # always loaded
    'data': [
        # 'views/account_letter_views.xml',
    ],
    
    'images': ['static/description/banner.gif'],
    'application': True,
    'installable': True,
    'auto_install': False,
}

