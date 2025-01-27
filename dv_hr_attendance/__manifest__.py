# -*- coding: utf-8 -*-
{
    'name': "Registro de Asistencias",

    'summary': "Registro de asistencia para personal",

    'description': """
Registro de asistencia para personal
    """,

    'author': "Develogers",
    'website': "https://develogers.com/",
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'LGPL-3',

    'category': 'Human Resources/Attendances',
    'version': '17.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'hr_attendance',
                'hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_view.xml',
        'views/hr_attendance_view.xml',
        'views/hr_shifts_view.xml',
        'views/hr_attendance_state_view.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'hr_attendance.assets_public_attendance': [
            'dv_hr_attendance/static/src/js/manual_selection_custom.js',
        ]
    },

}

