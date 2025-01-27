# -*- coding: utf-8 -*-
{
    'name': "Personalización de Empleados",

    'summary': """
        Módulo personalizado para Empleados""",

    'author': 'Develogers',
	'website': "https://develogers.com/",
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'Other proprietary',

    'category': 'Other',
    'version': '17.1',

    'depends': [
        'base',
        'hr',
        'project'
    ],

    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'report/template_email.xml',
        'views/view_employee_skill.xml',
        'views/view_employee_skill_report.xml',
        'views/view_alerta_renovacion.xml'
    ],
    'uninstall_hook': 'restore_original_view',
    
    'images': ['static/description/icon.png'],
    'application': True,
    'installable': True,
    'auto_install': False,
}

