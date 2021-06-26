# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class StockMoveLine(models.Model):
    """

    """
    _inherit = 'stock.move.line'

    repair_product_id = fields.Many2one('product.product',
                                        string='Parent Product Number')
    vehicle_number = fields.Char(string='Parent Serial Number')
    flight_hours = fields.Float(string='Flight Hours')
