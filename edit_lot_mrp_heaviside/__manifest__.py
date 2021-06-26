# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

{
    'name': "Edit LOT/Serial In MRP Heaviside",
    'summary': """""",
    'author': "S4 Solutions, LLC",
    'website': "https://www.sfour.io/",
    'version': '13.0.1.0.0',
    'license': "OPL-1",
    'category': 'MRP',
    'depends': [
        'edit_lot_mrp_base',
        'partial_serialization_base',
    ],
    'data': [
        'views/mrp_workorder_view.xml',
        'views/stock_view.xml'
    ],
    'installable': True,
}
