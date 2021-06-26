# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class StockWarnInsufficientQtyRepairOrder(models.TransientModel):
    """

    """
    _name = 'stock.warn.insufficient.qty.repair.order'
    _description = 'Stock Warn Insufficient Qty Repair Order'
    _inherit = 'stock.warn.insufficient.qty'

    repair_id = fields.Many2one('fleet.repair', string='Repair')

    def action_done(self):
        """

        :return:
        """
        self.ensure_one()
        return self.repair_id.action_repair_confirm()
