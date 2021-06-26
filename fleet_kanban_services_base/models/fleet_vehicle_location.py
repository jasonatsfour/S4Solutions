# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models, fields, api


class FleetVehicleLocation(models.Model):
    """

    """
    _name = 'fleet.vehicle.location'
    _description = 'Fleet Vehicle Location'

    name = fields.Char(copy=False)
