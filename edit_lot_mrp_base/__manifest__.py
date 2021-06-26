# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

{
    'name': "Edit LOT/Serial In MRP",
    'summary': """
In Odoo standard flow, it doesn't allow us to edit lot/serial 
once we completed Work order. We have added functionality to 
manage edit Lot/serial even after completed Work Order.
Once Manufacturing order is Marked as done we can not do any changes.""",
    'author': "S4 Solutions, LLC",
    'website': "https://www.sfour.io/",
    'version': '13.0.1.0.0',
    'license': "OPL-1",
    'category': 'MRP',

    # any module necessary for this one to work correctly
    'depends': [
        'mrp_workorder',
    ],

    # always loaded
    'data': [
        'views/mrp_workorder_view.xml',
    ],

    'installable': True,
}
