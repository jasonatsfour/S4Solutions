# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class FleetRepairTag(models.Model):
    """

    """
    _name = 'fleet.repair.tag'
    _description = 'Fleet Repair Tag'

    name = fields.Char(string='Name', copy=False, required=True)
