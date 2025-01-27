{
	'name': "Impuesto de Detracción en Facturas Electrónicas - Perú Enterprise",
	'summary': "Agregar impuesto de detracción en facturas electrónicas de Perú",

	'author': 'Develogers',
	'website': 'https://develogers.com',
	'support': 'https://develogers.com/helpdesk',
	'live_test_url': 'https://wa.link/2cc9dn',
	'license': 'Other proprietary',

	'category': 'Localization',
	'version': '17.0',

	'price': '49.99',
	'currency': 'USD',

	'depends': [
		'base',
		'l10n_pe_edi',
		'dv_l10n_pe_edi_date_due_list',
  		'dv_l10n_pe_account_detractions',
	],

	'data': [
		'views/report_invoice.xml',
	],

	'demo': [
		'demo/res_partner_bank_demo.xml',
	],
 
	'images': ['static/description/banner.png'],

	'application': True,
	'installable': True,
	'auto_install': False,
}
