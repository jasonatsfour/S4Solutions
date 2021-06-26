# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models


class MrpProduction(models.Model):
    """Inherit: MRP Production

    """
    _inherit = 'mrp.production'

    def _prepare_traceability(self, lines):
        """Prepare Traceability Lines.

        Prepare lines to manage the traceability for the MO.

        :param lines: MO Moves
        :return: List of dictionaries
        """
        vals = []
        for line in lines:
            vals.append({
                'production_id': self.id,
                'product_id': line.product_id.id,
                'move_line_id': line.id,
                'lot_id': line.lot_id.id,
                'qty_done': line.qty_done,
                'reference': line.reference,
                'operation_type': 'add'
            })
        return vals

    def post_inventory(self):
        """Inherited: Post Inventory

        Creates Traceability lines to manage Add/Remove Component on report.

        :return: True
        """
        res = super(MrpProduction, self).post_inventory()
        done_line = self.env['traceability.mark.done']
        move_env = self.env['stock.move.line']
        for order in self:
            line_ids = move_env.search([
                ('reference', '=', order.name)
            ])
            done_line.create(order._prepare_traceability(line_ids))
        return res
