# -*- coding: utf-8 -*-
{
    'name': "Código de barras en la órden de compra",

    'summary': """
        Módulo personalizado para agregar código de barras en la órden de compra.""",

    'author': 'Develogers',
	'website': "https://develogers.com/",
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'Other proprietary',

    'category': 'Other',
    'version': '17.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase', 'product', 'stock'],

    # always loaded
    'data': [
        'report/purchase_order_templates.xml',
    ],

    'images': ['static/description/banner.gif'],
    'application': False,
    'installable': True,
    'auto_install': False,
}

