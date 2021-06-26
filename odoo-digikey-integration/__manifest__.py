# -*- coding: utf-8 -*-
{
    'name': "Odoo Digikey Integration",

    'summary': """
        Odoo and digikey api integration""",

    'description': """
       To get part's prices of Digikey vendor.
    """,

    'author': "S4 Solutions, LLC",
    'website': "https://www.sfour.io/",

    
    'category': 'Purchase',
    'version': '11.0.4',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase'],   

    
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/token_schedular.xml',
        'views/connector.xml',

    ],
    'external_dependencies': {
       'python3': ['requests_oauthlib'],
    },

}