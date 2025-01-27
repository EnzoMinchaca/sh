{
    'name': """
        Consulta RUC y DNI con Integración a SUNAT Perú
    """,

    'summary': """
        Permite obtener datos del contacto registrando el DNI o RUC mediante una integración con SUNAT.
    """,

    'description': """
        Adds withholding tax move in invoices and creates the account seat. |
        Agrega impuesto de retención en facturas y crea la cuenta de retención.
    """,

	'author': 'Develogers',
    'website': 'https://develogers.com',
    'support': 'https://develogers.com/helpdesk',
    'live_test_url': 'https://wa.link/2cc9dn',
    'license': 'LGPL-3',

    'category': 'Localization',
    'version': '17.0',

    'price': 49.99,
    'currency': 'EUR',

    'depends': [
        'base',
        'dv_l10n_pe_partner_base',
    ],

    'data': [
        'views/res_config_settings_views.xml',
    ],

    'images': ['static/description/banner.gif'],

    'application': True,
    'installable': True,
    'auto_install': False,
}