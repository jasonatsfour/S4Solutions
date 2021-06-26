# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models, fields


class BomExplosionLine(models.Model):
    """BoM Explosion Lines

    """
    _name = 'bom.explosion.line'
    _description = 'BoM Explosion Lines'

    product_id = fields.Many2one('product.product', string='Product')
    lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial')
    bom_explosion_id = fields.Many2one("bom.explosion", string="BoM Explosion")
    partial_serialization_id = fields.Many2one(
        "vehicle.partial.serialization", string='Partial Serialization')
    level = fields.Integer(string="Level")
    product_qty = fields.Float(string="Quantity")
