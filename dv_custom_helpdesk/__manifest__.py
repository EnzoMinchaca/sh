# -*- coding: utf-8 -*-
{
    'name': "Personalización de Mesa de Ayuda",

    'summary': """
        Módulo personalizado para Mesa de Ayuda""",

    'author': 'Develogers',
	'website': "https://develogers.com/",
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'Other proprietary',

    'category': 'Other',
    'version': '17.1',

    'depends': [
        'base',
        'helpdesk',
        'helpdesk_timesheet',
        'website_helpdesk',
        'web',
        'dvl_contacts_custom',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/groups_rules.xml',
        'views/helpdesk_sla_views.xml',
        'views/helpdesk_views.xml',
        'views/timer_timer_views.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'dv_custom_helpdesk/static/src/fields/tickets_one2many/tickets_one2many.js',
            'dv_custom_helpdesk/static/src/fields/tickets_one2many/tickets_one2many.scss',
            'dv_custom_helpdesk/static/src/fields/tickets_one2many/tickets_one2many.xml',
            'dv_custom_helpdesk/static/src/estilos_kanban.scss',
            'dv_custom_helpdesk/static/src/fields/format_duration/format_duration.js',
            'dv_custom_helpdesk/static/src/fields/format_duration/format_duration.xml',
            # 'dv_custom_helpdesk/static/src/xml/tickets_template.xml',
        ],
    },

    'images': ['static/description/banner.gif'],
    'application': True,
    'installable': True,
    'auto_install': False,
}

