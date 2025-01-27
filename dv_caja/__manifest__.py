# -*- coding: utf-8 -*-
{
    'name': "Caja chica",

    'summary': """
        Módulo para la administración de cajas chicas""",

	'author': 'Develogers',
    'website': 'https://develogers.com',
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://wa.me/message/NN37LBBZC5TQA1',
    'license': 'Other proprietary',

    'category': 'Invoicing',
    'version': '17.0',

    'depends': ['base', 'account','web'],

    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'views/caja_view.xml',
        'views/account_journal_view.xml'
    ],
    
    'images': ['static/description/banner.gif'],
    'auto_install': False,
	'application': True,
	'installable': True,
}

