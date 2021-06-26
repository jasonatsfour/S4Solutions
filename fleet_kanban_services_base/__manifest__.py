# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

{
    'name': "Fleet Kanban Services",
    'summary': """
This module will managing Vehicle, its Availability, Status, Discrepancy,
Service Request and Fleet Repair Order.
    """,
    'category': 'Fleet',
    'author': "S4 Solutions, LLC",
    'website': "https://www.sfour.io/",
    'version': '13.0.1.0.0',
    'license': "OPL-1",

    # any module necessary for this one to work correctly
    'depends': [
        'product',
        'fleet',
        'account',
        'stock',
        'partial_serialization_base'
    ],

    # always loaded
    'data': [
        'security/record_rule_view.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/vehicle_status_data.xml',
        'data/service_generate_cron_data.xml',
        'data/hide_menuitem.xml',
        'views/assets.xml',
        'views/fleet_repair_stage_views.xml',
        'views/fleet_repair_tag_views.xml',
        'views/fleet_repair_type_views.xml',
        'views/fleet_repair_view.xml',
        'views/fleet_service_type_views.xml',
        'views/fleet_vehicle_available_views.xml',
        'views/fleet_vehicle_cost_views.xml',
        'views/fleet_vehicle_location_views.xml',
        'views/fleet_vehicle_state_views.xml',
        'views/fleet_vehicle_status_view.xml',
        'views/fleet_vehicle_view.xml',
        'views/hw_failure_mode_views.xml',
        'views/observed_during_views.xml',
        'views/recurring_service_plan_views.xml',
        'views/service_request_template_views.xml',
        'views/stock_move_view.xml',
        'views/stock_warehouse_views.xml',
        'views/vehicle_discrepancy_state_views.xml',
        'views/vehicle_discrepancy_type_views.xml',
        'views/vehicle_discrepancy_views.xml',
        'views/vehicle_flight_log_views.xml',
        'views/vehicle_service_state_view.xml',
        'views/vehicle_services_views.xml',
        'report/report_vehicle_barcode.xml',
        'report/report_views.xml',
        'wizard/repair_order_creation.xml',
        'wizard/stock_warn_insufficient_qty_repair_order_views.xml',
        'wizard/apply_to_multiple_vehicle_view.xml',
        'views/menu.xml'
    ],

    'qweb': [
        "static/src/xml/kanban_services.xml",
    ],

    'installable': True,
}
