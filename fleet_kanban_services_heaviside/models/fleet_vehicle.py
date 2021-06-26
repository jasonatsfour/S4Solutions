# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models, fields


class FleetVehicle(models.Model):
    """

    """
    _inherit = 'fleet.vehicle'

    last_sr_id = fields.Many2one('vehicle.services',
                                 string="Last Service By Date")
    last_sr_date = fields.Date(string="Last Service Date")
