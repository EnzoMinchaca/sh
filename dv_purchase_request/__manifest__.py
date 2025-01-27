# -*- coding: utf-8 -*-
{
    'name': "Solicitud de compras",

    'summary': """
        Módulo personalizado para crear solicitudes de compras""",

    'author': 'Develogers',
	'website': "https://develogers.com/",
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'Other proprietary',

    'category': 'Other',
    'version': '17.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase', 'hr', 'account', 'purchase_stock', 'dvl_contacts_custom'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/purchase_request_data.xml',
        'views/purchase_request_views.xml',
        'views/purchase_request_line_views.xml',
        'views/purchase_request_rule_views.xml',
        'views/purchase_order_views.xml',
        'views/account_account_views.xml',
        'views/menu_views.xml',
    ],
    'images': ['static/description/banner.gif'],
    'application': True,
    'installable': True,
    'auto_install': False,
}

