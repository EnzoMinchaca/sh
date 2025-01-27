# -*- coding: utf-8 -*-
{
    'name': "Pack de Productos",

    'summary': """
        Módulo para la creación de paquetes de productos""",

    'author': 'Develogers',
	'website': "https://develogers.com/",
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'Other proprietary',

    'category': 'Product',
    'version': '17.0',

    'depends': ['base',
                'product',
                'sale', 
                'sale_product_configurator',
                'stock',
                'stock_account',
                'sale_stock'],
    'data': [
        'views/product_template_views.xml',
        'views/product_attribute_views.xml',
        'views/product_attribute_views_form.xml',
        'views/sale_order_line_views.xml',
        'views/stock_picking_views.xml',
        'views/report_deliveryslip.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sale_product_configurator/static/src/js/product_template_attribute_line/product_template_attribute_line.js',
            'dv_products_packs/static/src/js/product_template_attribute_line.js',
            'dv_products_packs/static/src/xml/product_template_attribute_line.xml',
        ],
    },

    'images': ['static/description/banner.gif'],
    'application': False,
    'installable': True,
    'auto_install': False,
}
