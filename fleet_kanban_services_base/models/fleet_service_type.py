# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models, fields, api


class FleetServiceType(models.Model):
    _inherit = 'fleet.service.type'

    inactive = fields.Boolean(string="Inactive")
    moc = fields.Boolean(string="MOC")
    category = fields.Selection([
        ('contract', 'Contract'),
        ('service', 'Service')
    ], string='Category', required=True, default='service',
        help='Choose whether the service refer to contracts, '
             'vehicle services or both')

