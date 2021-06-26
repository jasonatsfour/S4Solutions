# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

{
    'name': "Fleet Management",
    'summary': """ It will install all related Modules for Fleet""",
    'description': """This module will install following modules\n
    1. as_built_report_base\n
    2. edit_lot_mrp_base\n
    3. fleet_kanban_services_base\n
    4. fleet_traceability_base\n
    5. manufacturing_traceability_base\n
    6. partial_serialization_base\n
    7. serial_lot_status_base
    """,
    'category': 'Fleet',
    'author': "S4 Solutions, LLC",
    'website': "https://www.sfour.io/",
    'version': '13.0.1.0.1',
    'license': "OPL-1",
    'depends': [
        'as_built_report_base',
        'edit_lot_mrp_base',
        'fleet_kanban_services_base',
        'fleet_traceability_base',
        'manufacturing_traceability_base',
        'partial_serialization_base',
        'serial_lot_status_base',
    ],
    'installable': True,
}
