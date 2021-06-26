# -*- coding: utf-8 -*-

{
    'name' : 'Zipline Barcode Enhancements',
    'version' : '13.0.1.1',
    'summary': 'Zipline Barcode Enhancements',
    'author': "S4 Solutions, LLC",
    'website': "https://www.sfour.io/",
    'sequence': 1,
    'description': """
        Zipline Barcode Enhancements
    """,
    'category': 'mrp',
    'images' : [],
    'depends' : ['base', 'stock_barcode'],
    'data': [
        'views/stock_barcode_templates.xml',
        'views/stock_picking_views_new.xml',

    ],
    'qweb': [
        "static/src/xml/stock_barcode.xml",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

