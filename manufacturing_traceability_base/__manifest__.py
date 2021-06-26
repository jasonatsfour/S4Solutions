# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

{
    'name': "Manufacturing Traceability",
    'summary': """
This module is dependent on Partial Serialization in which we can manage
Product tracking as  Partially Serialized.
    """,
    'description': """
In odoo standard Manufacturing Order, it allow user to add Lot/Serial only
when Product Tracking is either by Lot or Serial.
We have added additional conditions so that If Product is Partially
Serialized then also system will ask for Lot/Serial.
""",
    'category': 'Fleet',
    'author': "S4 Solutions, LLC",
    'website': "https://www.sfour.io/",
    'version': '13.0.1.0.1',
    'license': "OPL-1",

    # any module necessary for this one to work correctly
    'depends': [
        'partial_serialization_base',
        'serial_lot_status_base',
        'mrp_workorder',
        'quality_mrp_workorder',
        'mrp'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/mrp_split_wizard.xml',
        'views/mrp_production_views.xml',
        'views/mrp_view.xml',
        'views/mrp_workorder_views.xml',
        'views/res_company_view.xml',
        'views/res_config_view.xml',
        'views/stock_move_view.xml',
        'views/stock_production_lot_view.xml',
        'wizard/mrp_product_produce_views.xml',
        'wizard/advance_failure_wizard.xml',
        'views/stock_picking_type_views.xml',
        'views/templates.xml',
        'views/quality_check.xml',
        'views/mrp_workcenter.xml',
    ],

    'qweb': ['static/src/xml/list_view_buttons.xml'],

    'installable': True,
}
