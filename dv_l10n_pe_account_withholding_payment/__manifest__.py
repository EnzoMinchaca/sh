{
    'name': """
        Registro de pago de Retenciones y Detracciones - Perú |
        Withholding and Detraction Payment Register - Peru
    """,

    'summary': """
        Permite registrar pagos de retenciones y detracciones de facturas de clientes y proveedores.
    """,

	'author': 'Develogers',
    'website': 'https://develogers.com',
    'support': 'https://develogers.com/helpdesk',
    'live_test_url': 'https://wa.link/2cc9dn',
    'license': 'Other proprietary',

    'category': 'Localization',
    'version': '17.1',
    
    'price': 49.99,
    'currency': 'EUR',

    'depends': [
        'base',
  		'dv_l10n_pe_account_retentions',
    ],

    'data': [
        'views/account_journal_views.xml',
        'wizard/account_payment_register_views.xml',
    ],
    
    'images': ['static/description/banner.png'],
    
    'auto_install': False,
	'application': True,
	'installable': True,
}
