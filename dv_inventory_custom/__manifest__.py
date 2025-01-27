# -*- coding: utf-8 -*-
{
    'name': "Personalización de Inventario",

    'summary': """
        Módulo para personalizar el Inventario""",

    'author': 'Develogers',
	'website': "https://develogers.com/",
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'Other proprietary',

    'category': 'Product',
    'version': '17.1',

    'depends': [
        'base',
        'stock',
        'l10n_pe_edi',
        'l10n_pe_edi_stock'],
    'data': [
        'views/views_stock_picking.xml',
        'views/views_stock_move_line.xml'
    ],

    'images': ['static/description/banner.gif'],
    'application': False,
    'installable': True,
    'auto_install': False,
}
