# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models, fields


class FleetVehicleAvailable(models.Model):
    """

    """
    _name = 'fleet.vehicle.available'
    _description = 'Fleet Vehicle Available'

    name = fields.Char(copy=False)
    is_grounded = fields.Boolean(string="Grounded")
    is_available = fields.Boolean(string="Available")
    is_in_repair = fields.Boolean(string="In Work")
    moc = fields.Boolean(string="MOC")
    color = fields.Integer(string='Color Index', default=10,
                           help="Kanban Card Color/Availability Mapping:\n"
                                "[ Enter value between 0-11]\n"
                                "0 - Blank\n"
                                "1 - Red\n"
                                "2 - Light Orange\n"
                                "3- Yellow\n"
                                "4 - Blue\n"
                                "5 - Magenta\n"
                                "6 - Dark Orange\n"
                                "7- Teal\n"
                                "8 - Navy Blue\n"
                                "9 - Crimson\n"
                                "10 -Green\n"
                                "11 - Purple")
