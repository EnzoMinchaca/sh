# -*- coding: utf-8 -*-
{
    'name': "Personalización de Documentos de Ventas",

    'summary': """
        Módulo personalizado para creacion de documentos de Ventas""",

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
                'web'],

    'data': [
        'reports/sale_order_template.xml',
        'reports/report.xml',
        'views/view_res_company.xml',
        'views/view_sale_order.xml'
    ],

    'images': ['static/description/icon.png'],
    'auto_install': False,
	'application': True,
	'installable': True,
}

