{
    'name': """
        Facturas con Impuesto de Detracción Perú
    """,

    'summary': """
        Permite generar facturas con impuestos de detracción. |
        Allows to generate invoices with detraction taxes.
    """,

	'author': 'Develogers',
    'website': 'https://develogers.com',
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://wa.me/message/NN37LBBZC5TQA1',
    'license': 'Other proprietary',

    'category': 'Localization',
    'version': '17.0',
    
    'price': 49.99,
    'currency': 'EUR',

    'depends': [
        'base',
        'account',
        'l10n_latam_invoice_document',
        'dv_l10n_pe_account_payment_term_foreign_currency',
    ],

    'data': [
        'security/ir.model.access.csv',
        'data/l10n_pe.spot.code.csv',
        'views/account_move_views.xml',
        'views/l10n_pe_spot_code_views.xml',
        'views/product_template_views.xml', # TODO: compatibilidad con l10n_pe_edi, agregar algun invisible para que no se vea duplicado
        'views/res_config_settings_views.xml',
        'views/menu_item_views.xml',
    ],
    
    'images': ['static/description/banner.gif'],
    
    'auto_install': False,
	'application': True,
	'installable': True,
}
