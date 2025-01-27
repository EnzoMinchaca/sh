# -*- coding: utf-8 -*-
{
    'name': "Descuentos sucesivos para Ventas",

    'summary': """
        Módulo personalizado para realizar descuentos sucesivos en las Ventas""",

    'author': 'Develogers',
	'website': "https://develogers.com/",
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'Other proprietary',

    'category': 'Other',
    'version': '17.0',

    'depends': ['base',
                'sale',
                'mail',
                'web',
                'bus'],

    'data': [
        'security/ir.model.access.csv',
        'views/sale_views.xml',
        'data/template_discounts.xml',
        'wizard/successive_discounts.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'dv_sales_successive_discounts/static/src/js/notification.js',
        ]
    },

    'images': ['static/description/icon.png'],
    'application': False,
    'installable': True,
    'auto_install': True,
}

