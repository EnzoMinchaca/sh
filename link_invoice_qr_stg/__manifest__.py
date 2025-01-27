{
    "name": "QR In Invoice, QR Code, QR Invoice, QR Download",
    "license": "OPL-1",
    "currency" : 'EUR',
    "price" : '9.0',
    "category":'Sales',
    "version": "17.0.1.0.0",
    "sequence":1,
    "summary": "URL to QR code in odoo invoice, QR code invoice, link to QR code in invoice odoo",
    "description": """
    Create amazing invoice with QR code from URL into invoice odoo app for Odoo, See your created invoice with qr code using url and we have extended the module in odoo, very useful module for invoice qr code in odoo.
    """,
    "author": "Steigern Tech LLP",
    "website": "https://steigerntech.com/",
    "support" : "steigerntech@gmail.com",
    "live_demo_url": "https://youtu.be/pNOFkS2iHy4",
    "depends": ["base", "account", "sale", "stock"], 
    "data": [
        "views/account_move_view.xml",
        "report/account_invoice_sent.xml",
        "views/config.xml",
    ],

    'images':["static/description/banner.gif"],
    
    "installable": True,
    "application": True,
    "auto_install": False,
    
}
