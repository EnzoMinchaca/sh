# -*- coding: utf-8 -*-
{
    'name': "Template Filter CRM",

    'summary': """
        Modulo personalizado para filtrar plantillas por tipo de pipeline en CRM""",

    'category': 'Other',
    'version': '17.1',

    'depends': ['base',
                'crm',
                'mail',
                ],

    "data": [
        "views/mail_template_views.xml",
    ],
    
    'application': True,
    'installable': True,
    'auto_install': False,
}

