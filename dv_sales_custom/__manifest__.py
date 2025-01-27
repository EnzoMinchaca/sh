# -*- coding: utf-8 -*-
{
    'name': "Personalización de Ventas",

    'summary': """
        Módulo personalizado para Ventas""",

    'author': 'Develogers',
	'website': "https://develogers.com/",
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'Other proprietary',

    'category': 'Other',
    'version': '17.0',

    'depends': ['base',
                'product',
                'stock',
                'sale',
                'web',
                'purchase',
                'hide_cost_price'],

    'data': [
        'views/product_search.xml',
        'views/product_views.xml',
        'views/sale_views.xml',
        'views/purchase_views.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'dv_sales_custom/static/src/js/search.js',
        ],
    },

    'images': ['static/description/icon.png'],
    'application': False,
    'installable': True,
    'auto_install': True,
}

