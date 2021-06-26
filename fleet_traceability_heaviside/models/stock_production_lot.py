# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import api, fields, models, _


class StockProductionLot(models.Model):
    """Inherit: Lot/Serial Number

    """
    _inherit = 'stock.production.lot'

    cumulative_flight_hours = fields.Float(string='Cumulative Flight Hours',
                                           track_visibility='onchange')
