# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class StockWarehouse(models.Model):
    """

    """
    _inherit = 'stock.warehouse'

    add_source_location = fields.Many2one(
        'stock.location', string='Source Location for Adds',
        help='Set Source Location for Add.')
    add_destination_location = fields.Many2one(
        'stock.location', string='Destination Location for Adds',
        help='Set Destination Location for Add.')
    remove_source_location = fields.Many2one(
        'stock.location', string='Source Location for Removes',
        help='Set Source Location for Remove.')
    remove_destination_location = fields.Many2one(
        'stock.location', string='Destination Location for Removes',
        help='Set Destination Location for Remove.')
