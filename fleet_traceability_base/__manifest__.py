# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

{
    'name': 'As-Maintained Traceability',
    'summary': """
This module will support creation and maintenance of As-Maintained
structures of installed components for serialized products.""",
    'description': """
This module will support creation and maintenance of As-Maintained
structures of installed components for serialized products.""",
    'author': 'S4 Solutions, LLC',
    'website': 'https://www.sfour.io/',
    'category': 'Fleet',
    'version': '13.0.1.0.0',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'fleet_kanban_services_base',
        'serial_lot_status_base'
    ],

    # always loaded
    'data': [
        'security/as_maintained_security.xml',
        'security/ir.model.access.csv',
        'data/as_maintained_report_data.xml',
        'data/ir_sequence_data.xml',
        'views/add_remove_lot_template.xml',
        'views/fleet_repair_view.xml',
        'views/fleet_traceability_base_assets.xml',
        'views/fleet_vehicle_view.xml',
        'views/stock_production_lot_views.xml',
        'views/stock_production_quant_view.xml',
        'views/vehicle_services_view.xml',
    ],
    'qweb': [
        'static/src/xml/as_maintained_report.xml',
    ],
    'installable': True,
}
