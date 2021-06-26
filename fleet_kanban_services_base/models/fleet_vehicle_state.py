# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models, fields, api


class FleetVehicleState(models.Model):
    """

    """
    _inherit = 'fleet.vehicle.state'

    is_grounded = fields.Boolean(string="Is Grounded?", copy=False)
