{
    'name': """
        Facturas Electrónicas con Cuotas de Pago - Addon Facturación Electrónica Perú |
        Electronic Invoices with Payment Terms - Electronic Invoicing Peru addon
    """,
    'summary': """
        Agrega cuotas de pago en facturas electrónicas de Perú
    """,

    'author': 'Develogers',
    'website': 'https://develogers.com',
    'support': 'https://develogers.com/helpdesk',
    'live_test_url': 'https://wa.link/2cc9dn',
    'license': 'Other proprietary',

    'category': 'Localization',
    'version': '16.0',

    'price': '49.99',
    'currency': 'USD',

    'depends': [
        'base',
        
        # Development
		'l10n_pe_edi', 
		#'dv_l10n_pe_edi',
    ],

    'data': [
        'views/report_invoice.xml',
    ],

    'images': ['static/description/banner.png'],

    'application': True,
    'installable': True,
    'auto_install': False,
}
