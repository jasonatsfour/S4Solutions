# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class StockOperationType(models.Model):
    _inherit = 'stock.picking.type'

    backflush_on_mo_completion = fields.Boolean(string="Backflush on WO Completion", default=False)
    splits_allowed = fields.Boolean(string="Splits Allowed", default=False)
    splits_operation_type_id = fields.Many2one('stock.picking.type',
                                               string="Split Operation Type",
                                               domain=[('code', '=', 'mrp_operation')])
    rework = fields.Boolean(string="Rework")
    default_component_to_parent_product_id = fields.Many2one('product.product',
                                                             string="Default Component to Parent Product")
    operation_edit_allowed = fields.Boolean(string="Operation Edits Allowed")
    component_list_edit_allowed = fields.Boolean(string="Components List Edits Allowed")
