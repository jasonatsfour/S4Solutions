# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

{
    'name': "Partial Serialization for Fleet and Manufacturing",
    'summary': """Partial Serialization for Fleet and Manufacturing""",
    'category': 'Fleet',
    'author': "S4 Solutions, LLC",
    'website': "https://www.sfour.io",
    'version': '13.0.1.0.0',
    'license': "OPL-1",

    # any module necessary for this one to work correctly
    'depends': [
        'stock'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/partial_serialization_view.xml',
        'views/product_view.xml',
        'views/stock_move_line_views.xml'
    ],
    'installable': True,
}
