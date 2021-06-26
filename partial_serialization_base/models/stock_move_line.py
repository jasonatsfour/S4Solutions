# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class StockMoveLine(models.Model):
    """Move Lines

    Fields:
    product_tracking: Related - Product
    partial_serialization_id: Related - Product -> partial_serialization_id
    partial_serialization_type: Related - Product ->
    partial_serialization_id -> traceability_type (i.e. Lot ro Serial)
    """
    _inherit = "stock.move.line"

    product_tracking = fields.Selection(
        related='product_id.tracking', string="Product Tracking")

    partial_serialization_id = fields.Many2one(
        related="product_id.partial_serialization_id",
        string="Partial Serialization", store=True)

    partial_serialization_type = fields.Selection(
        related="product_id.partial_serialization_id.traceability_type",
        string="Partial Tracking", readonly=True, store=True)
