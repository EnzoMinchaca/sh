# -*- coding: utf-8 -*-
{
    'name': "Grupos de Acceso",

    'summary': """
        Módulo personalizado para Grupos de Acceso""",

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
        'crm', 
        'sales_team', 
        'dv_crm_project_custom',
        'sale_crm',
    ],

    # always loaded
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'views/menu_views.xml',
        'views/crm_lead_views.xml',
        'views/mail_compose_message_views.xml',
        'views/project_project_views.xml',
    ],
    
    'images': ['static/description/banner.gif'],
    'application': False,
    'installable': True,
    'auto_install': False,
}

