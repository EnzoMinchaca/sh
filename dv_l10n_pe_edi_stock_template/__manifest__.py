# -*- coding: utf-8 -*-
{
    'name': "Formato de Guias de Remisión Electronica - Perú",

    'summary': "False",

    'author': 'Develogers',
    'website': 'https://develogers.com',
    'support': 'https://develogers.com/helpdesk',
    'live_test_url': 'https://wa.link/2cc9dn',
    'license': 'Other proprietary',

    'category': 'Extra Tools',
    'version': '1.0',

    'price': '49.99',
    'currency': 'USD',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'l10n_pe_edi_stock',
        'l10n_latam_invoice_document',
        ],

    'data': [
        'templates/external_layout_guide_remission_A4.xml',
        'templates/report_guide_remission.xml',
    #    'templates/external_layout_invoice_A4.xml',
    #    'templates/report_invoice.xml',
        'views/stock_view_picking.xml',
    ],
    
    'images': ['static/description/banner.png'],

    'application': True,
    'installable': True,
    'auto_install': False,
}

