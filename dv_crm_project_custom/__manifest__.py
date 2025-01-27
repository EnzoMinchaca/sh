# -*- coding: utf-8 -*-
{
    'name': "Personalización de CRM",

    'summary': """
        Módulo personalizado para CRM""",

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
                'crm_helpdesk',
                'sale_crm',
                'sale_project',
                'sales_team',
                'project',
                'project_enterprise',
                'sale_timesheet',
                'hr_timesheet',
                'mail',
                'mass_mailing',
                'web',
                'website_crm',
                'dvl_contacts_custom',],

    # always loaded
    'data': [
        'data/project_data.xml',
        'data/mail_message_subtype_data.xml',
        'data/ir_action_data.xml',
        'data/teams_data.xml',
        'data/cron_task_alert.xml',
        'security/ir.model.access.csv',
        'security/security_groups.xml',
        'wizard/crm_lead_not_offered_views.xml',
        'views/crm_lead_views.xml',
        'views/crm_public_lead_views.xml',
        'views/crm_private_lead_views.xml',
        'views/crm_not_offered_reason_views.xml',
        'views/project_project_views.xml',
        'views/project_category_views.xml',
        'views/menu_views.xml',
        'wizard/generate_task.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'dv_crm_project_custom/static/src/js/button_tree_generate_task.js',
            'dv_crm_project_custom/static/src/js/button_kanban_generate_task.js',
            'dv_crm_project_custom/static/src/xml/button_tree_generate_task.xml',
            'dv_crm_project_custom/static/src/xml/button_kanban_generate_task.xml',
            'dv_crm_project_custom/static/src/js/kanban_stage_update.js',
        ]
    },
    
    'images': ['static/description/banner.gif'],
    'application': True,
    'installable': True,
    'auto_install': False,
}

