{
    'name': """
      Estilo A4 Light para Facturación Electrónica - Perú |
      A4 Light Style for Electronic Invoicing - Peru
    """,
    'summary': """
      Agrega un estilo personalizado A4 Light para la impresión de facturas electrónicas.
    """,

    'author': 'Develogers',
    'website': 'https://develogers.com',
    'support': 'https://develogers.com/helpdesk',
    'live_test_url': 'https://wa.link/2cc9dn',
    'license': 'Other proprietary',

    'category': 'Localization',
    'version': '17.0',

    'price': '29.99',
    'currency': 'USD',

    'depends': [
        'base',
        'dv_l10n_pe_edi_date_due_list',
        'l10n_pe_edi',
        'sale_management',
        'dv_account_letter',
        #'dv_l10n_pe_edi',
    ],

    'data': [
        'views/account_move_views.xml',
        'template/external_layout_invoice_A4.xml',
        'template/report_invoice.xml',
    ],
    'images': ['static/description/banner.png'],

    'application': True,
    'installable': True,
    'auto_install': False,

}
