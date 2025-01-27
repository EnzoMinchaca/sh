# -*- coding: utf-8 -*-
{
    'name': "Orden de columnas en Kanban",

    'summary': """
        Módulo personalizado para ordenar las columnas en Kanban""",

    'author': 'Develogers',
	'website': "https://develogers.com/",
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'Other proprietary',

    'category': 'Other',
    'version': '17.1',

    'depends': ['crm', 'web', 'dv_crm_project_custom'],

    'data': [
        # 'security/ir.model.access.csv',
        'views/crm_stage.xml',
        'views/crm_lead.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'dv_kanban_column_order/static/src/js/kanban_stage_order.js',
        ]
    },
    
    'images': ['static/description/banner.gif'],
    'application': True,
    'installable': True,
    'auto_install': False,
}

