# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class VehicleDiscrepancyType(models.Model):
    """

    """
    _name = 'vehicle.discrepancy.type'
    _description = 'Vehicle Discrepancy Type'

    name = fields.Char(string='Name')
