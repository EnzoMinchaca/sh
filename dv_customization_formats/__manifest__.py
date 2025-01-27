{
    'name': "Generación de Reportes de Cotización y Facturas de Clientes",

    'summary': """
        Módulo para generación de Reportes de Cotización y Facturas de Clientes""",

	'author': 'Develogers',
    'website': 'https://develogers.com',
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://wa.me/message/NN37LBBZC5TQA1',
    'license': 'Other proprietary',

    'category': 'Invoicing',
    'version': '17.0',

    'depends': ['base','sale','l10n_pe_edi','account','stock'],

    "data": [
        "views/sale_order_views.xml",
        "views/config.xml",
        "views/account_move_view.xml",
        "template/external_layout_invoice_A4.xml",
        "template/report_invoice.xml",
        "template/report_invoice_second.xml",
    ],

    'images': ['static/description/icon.png'],
    
    'application': True,
    'installable': True,
    'auto_install': False,
}

