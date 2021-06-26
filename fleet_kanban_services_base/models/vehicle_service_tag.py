# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class VehicleServiceTag(models.Model):
    """

    """
    _name = 'vehicle.service.tag'
    _description = 'Vehicle Service Tag'

    name = fields.Char(string='Name', copy=False, required=True)
