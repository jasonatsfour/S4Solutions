# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class VehicleDiscrepancyState(models.Model):
    """

    """
    _name = 'vehicle.discrepancy.state'
    _description = 'Vehicle Discrepancy State'

    name = fields.Char(string='Name')
