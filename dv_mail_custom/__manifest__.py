# -*- coding: utf-8 -*-
{
    'name': "Personalización de Mensajes",

    'summary': """
        Módulo personalizado que modifica comportamientos y vistas del apartado de Mail""",

    'author': 'Develogers',
	'website': "https://develogers.com/",
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'Other proprietary',

    'category': 'Other',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'mail',
                'web'
                ],

    # always loaded
    'data': [
        'views/compose_message_view.xml'
    ],

    'assets': {
        'web.assets_backend': [
            'dv_mail_custom/static/src/js/checkbox_message.js',
            # 'dv_mail_custom/static/src/core/web/chatter.xml',
            # 'dv_mail_custom/static/src/core/web/chatter.scss'
        ]
    },
    
    'images': ['static/description/banner.gif'],
    'application': True,
    'installable': True,
    'auto_install': False,
}

