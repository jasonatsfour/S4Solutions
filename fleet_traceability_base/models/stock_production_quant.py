# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models, fields


class StockProductionQuant(models.Model):
    """

    """
    _name = 'stock.production.quant'
    _description = 'Stock Production Quant'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Lot/Serial Number', help="Unique Lot/Serial Number",
        default=lambda self: self.env['ir.sequence'].next_by_code(
            'stock.production.quant'), required=True)
    product_id = fields.Many2one(
        'product.product', string='Product', required=True,
        domain=[('type', 'in', ['product', 'consu'])])
    ref = fields.Char(
        string='Product Number', related='product_id.default_code',
        help="Product number in case it differs from "
             "the manufacturer's lot/serial number")
    product_uom_id = fields.Many2one(
        'uom.uom', string='Unit of Measure',
        related='product_id.uom_id', store=True)
    quant_ids = fields.One2many('stock.quant', 'lot_id', string='Quants',
                                readonly=True)
    create_date = fields.Datetime(string='Creation Date')
    product_qty = fields.Float(string='Quantity', compute='_product_qty')
    lot_version = fields.Integer(string='Lot Version', default=1)
    lot_ids = fields.Many2many('stock.production.lot',
                               string='Installed Location')
    is_non_traceable = fields.Boolean(string='Is Non-Traceable', default=True)

    def _product_qty(self):
        """

        :return:
        """
        for lot in self:
            # Only care for the quants in internal or transit locations.
            quants = lot.quant_ids.filtered(
                lambda q: q.location_id.usage in ['internal', 'transit']
            )
            lot.product_qty = sum(quants.mapped('quantity'))
