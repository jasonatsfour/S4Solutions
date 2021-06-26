# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class VehicleServiceType(models.Model):
    """

    """
    _name = 'vehicle.service.type'
    _description = 'Vehicle Service Type'
    _inherit = ['mail.thread']

    name = fields.Char(string='Name', copy=False, required=True)
    sequence = fields.Integer(string='Sequence')
