{
    'name': "Pago Masivo de Facturas",

    'summary': 
    '''
    Módulo que tiene como funcionalidad realizar el pago masivo de facturas
    permitiendo seleccionar el monto exacto a pagar de cada factura.
    ''',

    'author': "Develogers",
    'website': "https://develogers.com/",
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'Other proprietary',

    'category': 'Accounting/Accounting',
    'version': '17.1',

    'depends': ['base','account'],

    'data': [
        # Security
        'security/ir.model.access.csv',
        # Views
        'views/account_button_retention.xml',
        'wizard/massive_payment_register.xml',
    ],

    'images': ['static/description/icon.png'],
    'application': True,
    'installable': True,
    'auto_install': False,
}

