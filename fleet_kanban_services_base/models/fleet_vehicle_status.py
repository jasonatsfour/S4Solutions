# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class FleetVehicleStatus(models.Model):
    """

    """
    _name = 'fleet.vehicle.status'
    _description = 'Fleet Vehicle Status'

    name = fields.Char(string='Name')
