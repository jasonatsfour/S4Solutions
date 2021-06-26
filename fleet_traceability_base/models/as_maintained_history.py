# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class AsMaintainedHistory(models.Model):
    """As Maintained History.

    To log history for services.
    """
    _name = 'as_maintained.history'
    _description = 'AS Maintained History'
    _rec_name = 'repair_order_line_id'

    lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial')
    origin_part_of_id = fields.Many2one(
        'stock.production.lot', string='Origin Lot/Serial')
    parent_lot_version = fields.Integer(string='Version')
    repair_order_line_id = fields.Many2one(
        'fleet.repair.line', string='Repair Order Line')
    lot_type = fields.Selection([
        ('add', 'Add'),
        ('remove', 'Remove')
    ], string='Type', default='add')
    as_maintained_parent_lot_id = fields.Many2one(
        'stock.production.lot', string='Installed Location')
    as_maintained_child_lot_id = fields.Many2one(
        'stock.production.lot', string='AS-Maintained Lot/Serial')
    product_id = fields.Many2one('product.product', string='Product')
    price_unit = fields.Float(
        string='Unit Price', digits='Product Price')
    product_uom_qty = fields.Float(
        string='Quantity', default=1.0, digits='Product Unit of Measure')
    location_id = fields.Many2one(
        'stock.location', string='Source Location', index=True)
    location_dest_id = fields.Many2one(
        'stock.location', string='Dest. Location', index=True)
