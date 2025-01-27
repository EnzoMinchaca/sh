# -*- coding: utf-8 -*-
{
    'name': "Personalización de CRM Adicional",

    'summary': """
        Nuevo módulo personalizado para CRM""",

    'author': 'Develogers',
	'website': "https://develogers.com/",
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'Other proprietary',

    'category': 'Other',
    'version': '17.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'crm',
                'web',
                'dv_crm_project_custom'],

    # always loaded
    'data': [
        'views/execute_action.xml',
        'views/views_crm_lead.xml'
    ],

    'assets': {
        'web.assets_backend': [
            'dv_crm_new_custom/static/src/js/update_kanban_view.js',
            'dv_crm_new_custom/static/src/js/crm_lead_sku.js'
        ]
    },
    
    'images': ['static/description/banner.gif'],
    'application': True,
    'installable': True,
    'auto_install': False,
}

