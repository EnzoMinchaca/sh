{
    'name': "Campos de localizacion peruana para los Contactos",

    'summary': "",

    'description': "",

	'author': 'Develogers',
    'website': 'https://develogers.com',
    'support': 'https://develogers.com/helpdesk',
    'live_test_url': 'https://wa.link/2cc9dn',
    'license': 'LGPL-3',

    'category': 'Localization',
    'version': '17.0',

    'price': 99.99,
    'currency': 'EUR',

    'depends': [
        'base',
        'base_setup',
        'l10n_pe',
    ],

    'data': [
        'data/ir_actions_server_data.xml',
        'data/l10n_pe.economic.activity.csv',
		'security/ir.model.access.csv',
        'views/l10n_pe_economic_activity_views.xml',
		'views/res_partner_views.xml',
        'views/res_config_settings_views.xml',
        'views/menuitem_views.xml',
	],

    'images': ['static/description/banner.gif'],

    'application': True,
    'installable': True,
    'auto_install': False,
}