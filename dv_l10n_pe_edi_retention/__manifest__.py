{
	'name': "Impuesto de Retención en Facturas Electrónicas de Ventas - Perú Enterprise",
	'summary': "Permite emitir facturas electrónicas con impuesto de retención en Perú Enterprise",

	'author': 'Develogers',
	'website': 'https://develogers.com',
	'support': 'https://develogers.com/helpdesk',
	'live_test_url': 'https://wa.link/2cc9dn',
	'license': 'Other proprietary',

	'category': 'Localization',
	'version': '17.1',

	'price': '49.99',
	'currency': 'USD',

	'depends': [
		'base',
		'l10n_pe_edi',
		'dv_l10n_pe_edi_date_due_list',
		'dv_l10n_pe_account_retentions',
  		'dv_l10n_pe_account_payment_term_foreign_currency',
		'dv_l10n_pe_edi_template_light',
	],

	'data': [
		'views/account_move_views.xml',
		'views/report_invoice.xml',
	],

	'images': ['static/description/banner.png'],

	'application': True,
	'installable': True,
	'auto_install': False,
}
