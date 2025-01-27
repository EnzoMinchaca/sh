# -*- coding: utf-8 -*-
{
    'name': "Reporte de Seguimiento de Comprobantes Pagados",

    'summary': """
        Módulo que realiza un reporte de seguimiento de los comprobantes pagados generándolo en PDF y excel.""",

    'author': 'Develogers',
	'website': "https://develogers.com/",
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'Other proprietary',

    'category': 'Accounting/Accounting',
    'version': '17.1',

    'depends': [
        'base', 
        'dv_account_letter',
        'account',
        'web',
        'dv_l10n_pe_edi_retention',
        'dv_account_followup_custom'
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/template_report.xml',
        'views/account_followup_paid.xml',
        'views/report.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'dv_account_followup_paid/static/src/js/button_tree_generate_pdf.js',
            'dv_account_followup_paid/static/src/xml/button_tree_generate_pdf.xml',
            'dv_account_followup_paid/static/src/js/open_move_line_related_widget.js',
            'dv_account_followup_paid/static/src/xml/open_move_line_related_widget.xml',
        ]
    },

    'images': ['static/description/icon.png'],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}