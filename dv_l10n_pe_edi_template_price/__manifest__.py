{
    'name': """
      Estilo A4 Light para Cotización - Peru
    """,
    'summary': """
      Agrega un estilo personalizado A4 Light para la impresión de cotizaciones.
    """,

    'author': 'Develogers',
    'website': 'https://develogers.com',
    'support': 'https://develogers.com/helpdesk',
    'live_test_url': 'https://wa.link/2cc9dn',
    'license': 'Other proprietary',

    'category': 'Sales/Sales',
    'version': '17.1',

    'depends': [
        'base',
        'sale',
        'l10n_pe_edi',
    ],

    "data": [
        "templates/external_layout_price_A4.xml",
        "templates/report_price.xml",
    ],
    'images': ['static/description/icon.png'],


    'application': True,
    'installable': True,
    'auto_install': False,

}
