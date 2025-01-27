# -*- coding: utf-8 -*-
{
    'name': "Automatización de WhatsApp",

    'summary': """
        Módulo para la automatización de mensajes de WhatsApp""",

    'author': 'Develogers',
	'website': "https://develogers.com/",
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'Other proprietary',

    'category': 'WhatsApp',
    'version': '17.1',

    'depends': ['base', 'whatsapp', 'mail', 'base_automation'],

    # always loaded
    'data': [
        'views/ir_actions_server_views.xml',
        'views/base_automation_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dv_whatsapp_automation/static/src/base_automation_actions_one2many_field.xml',
        ],
    },

    'images': ['static/description/banner.gif'],
    'application': False,
    'installable': True,
    'auto_install': True,
}

