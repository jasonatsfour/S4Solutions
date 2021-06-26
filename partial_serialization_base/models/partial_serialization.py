# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class VehiclePartialSerialization(models.Model):
    """Vehicle Partial Serialization

    With this object you can create different type of partial tracking.
    Like: Serial or Lot

    Fields:
    name
    description
    manufacturing_use: To allow use in manufacturing components
    fleet_use: To allow use in fleet parts
    traceability_type: either Lot or Serial
    """
    _name = 'vehicle.partial.serialization'
    _description = 'Vehicle Partial Serialization'

    name = fields.Char(string="Name")
    description = fields.Text(string="Description")
    manufacturing_use = fields.Boolean(string="Use in Manufacturing")
    fleet_use = fields.Boolean(string="Use in Fleet")
    traceability_type = fields.Selection([
        ('lot', 'By Lots'),
        ('serial', 'By Unique Serial Number')
    ], string="Type", default='lot')
