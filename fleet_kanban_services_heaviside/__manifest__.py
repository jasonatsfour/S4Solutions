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
        'views/fleet_vehicle_view.xml'
    ],

    'qweb': [
        "static/src/xml/kanban_services.xml",
    ],

    'installable': True,
}
