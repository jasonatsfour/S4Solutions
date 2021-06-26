# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api


class TraceabilityMarkDone(models.Model):
    """Traceability Lines.

    """
    _name = 'traceability.mark.done'
    _description = 'To Trace MO/Ro Move Lines.'
    _rec_name = 'reference'
    _order = 'id DESC'

    reference = fields.Char(string='Reference')
    operation_type = fields.Selection([
        ('add', 'Add'),
        ('remove', 'Remove')
    ], string="Operation")
    product_id = fields.Many2one('product.product', string="Product")
    production_id = fields.Many2one('mrp.production', string='Production')
    repair_id = fields.Many2one('repair.order', string='Repair')
    move_line_id = fields.Many2one('stock.move.line', string="Line")
    lot_id = fields.Many2one('stock.production.lot', string="Serial/Lot")
    qty_done = fields.Float(string="Quantity Done")
