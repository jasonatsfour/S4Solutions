# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class StockMove(models.Model):
    """

    """
    _inherit = 'stock.move'

    fleet_repair_id = fields.Many2one('fleet.repair', string='fleet.repair')
