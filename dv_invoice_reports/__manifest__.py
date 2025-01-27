# -*- coding: utf-8 -*-
{
    'name': "Generación de Reportes de Facturas",

    'summary': """
        Módulo para generación de Reportes de facturas según filtros aplicados""",

	'author': 'Develogers',
    'website': 'https://develogers.com',
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://wa.me/message/NN37LBBZC5TQA1',
    'license': 'Other proprietary',

    'category': 'Invoicing',
    'version': '17.0',

    'depends': ['base', 'account', 'sale', 'sale_management','web'],
    
    # Cargando estiloss css para el reporte pdf
    'assets': {
        'web.report_assets_common': [
            'dv_invoice_reports/static/src/css/styles.css',
            'dv_invoice_reports/static/src/css/font.css',
        ],
    },

    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'reports/report.xml',
        'reports/template_header_footer.xml',
        'reports/template_report_detallado.xml',
        'reports/template_report_general.xml',
        'views/report_view.xml',
    ],
    
    'images': ['static/description/banner.gif'],
    'auto_install': False,
	'application': True,
	'installable': True,
}

