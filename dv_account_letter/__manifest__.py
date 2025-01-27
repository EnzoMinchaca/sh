# -*- coding: utf-8 -*-
{
    'name': "Canje de Letras",

    'summary': """
        Módulo dedicado a la gestión de canje de letras.""",

    'author': 'Develogers',
	'website': "https://develogers.com/",
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'Other proprietary',

    'category': 'Accounting/Accounting',
    'version': '17.1',

    'depends': [
        'base', 
        'account_edi',
        'account_accountant',
        'l10n_latam_invoice_document', 
        'l10n_latam_base',
        'l10n_pe_edi',
        'account_reports',
        'account_debit_note',
        'account_followup',
    ],

    # always loaded
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'wizard/account_letter_bank_views.xml',
        'wizard/preview_payment_views.xml',
        'views/account_letter_views.xml',
        'views/account_letter_conf_views.xml',
        'views/account_letter_line_views.xml',
        'views/account_move_views.xml',
        'views/account_debit_note_views.xml',
        'views/menu_views.xml',
        'data/ir_sequence_data.xml',
    ],
    
    'images': ['static/description/banner.gif'],
    'application': True,
    'installable': True,
    'auto_install': False,
}

