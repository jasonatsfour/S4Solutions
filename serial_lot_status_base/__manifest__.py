# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

{
    'name': "Serial Lot Status Base",
    'summary': """ Managing Status on Lot/Serial""",
    'description': """This module is managed status for Serial Product.
When user create new Serial at that time by default it set "Available" Status.
Once we change product on hand quantity it set "Inventory".
When this is used in Manufacturing order or Repair Order it's status will be
set as "Installed" and if product is scrapped then it set as "Scrapped".
    """,
    'category': 'Inventory',
    'author': "S4 Solutions, LLC",
    'website': "https://www.sfour.io/",
    'version': '13.0.1.0.0',
    'license': "OPL-1",

    # any module necessary for this one to work correctly
    'depends': [
        'stock',
        'partial_serialization_base',
        'mrp',
        'quality'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/stock_production_lot_views.xml',
        'views/stock_lot_statuses_view.xml',
    ],
    'demo': [
        'data/data_lot_statuses.xml',
    ],
    'installable': True,
}
