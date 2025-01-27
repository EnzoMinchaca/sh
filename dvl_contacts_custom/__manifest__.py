# -*- coding: utf-8 -*-
{
    'name': "Personalización de Contactos",

    'summary': """
        Módulo personalizado para Contactos""",

    'author': 'Develogers',
	'website': "https://develogers.com/",
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'Other proprietary',

    'category': 'Other',
    'version': '17.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'contacts',
        'l10n_latam_base',
        'l10n_pe',
    ],

    # always loaded
    'data': [
        'security/contacts_custom_security.xml',
        'data/contact_types_data.xml',
        'security/ir.model.access.csv',
        'views/res_partner_view.xml',
        'views/res_partner_menu.xml',
        'views/contact_line.xml'
    ],
    # 'post_init_hook': 'post_init_hook',
    'images': ['static/description/icon.png'],
    'application': False,
    'installable': True,
    'auto_install': True,
}

