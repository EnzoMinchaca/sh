{
    'name': "Impuesto de Retención - Perú",
    'summary': "Agrega tablas y campos impuesto de retención.",

    'author': 'Develogers',
    'website': 'https://develogers.com',
    'support': 'https://develogers.com/helpdesk',
    'live_test_url': 'https://wa.link/2cc9dn',
    'license': 'Other proprietary',

    'category': 'Localization',
    'version': '17.0',

    'price': 149.99,
    'currency': 'EUR',

    'depends': [
        'base',
        'account',
        'l10n_pe',
    ],

    'data': [
        'data/l10n_pe.withholding.code.csv',
        'security/ir.model.access.csv',
        'views/l10n_pe_withholding_code_views.xml',
        'views/res_company_views.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
        'views/menuitem_views.xml',
    ],

    'images': ['static/description/banner.png'],

    'auto_install': False,
    'application': True,
    'installable': True,
}
