# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

{
    'name': 'As-Built Traceability Report',
    'category': 'Mrp',
    'summary': """
This module will supports Tracebility based on Manufacturing Order. 
It also include modification on existig Manufacturing Order using 
Odoo standard Repair Order Operations.
""",
    'author': 'S4 Solutions, LLC',
    'website': 'https://www.sfour.io/',
    'version': '13.0.1.0.0',
    'license': 'OPL-1',
    'depends': [
        'mrp',
        'stock',
        'repair',
        'serial_lot_status_base'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/mrp_production_views.xml',
        'views/product_product_views.xml',
        'views/product_template_views.xml',
        'views/repair_view.xml',
        'views/stock_picking_views.xml',
        'views/stock_production_lot_views.xml',
        'views/stock_scrap_views.xml',
        'views/traceability_mark_done_views.xml',
        'views/traceability_report_view.xml',
    ],
    'qweb': [
        'static/src/xml/template_view.xml',
        'static/src/xml/report_mrp_line.xml',
    ],
    'installable': True,
    'auto_install': False,
}
