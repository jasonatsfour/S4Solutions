# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models, api, fields


class StockMoveLine(models.Model):
    """Inherited: Production Moves

    Fields:
    production_state: Related - WO -> PO -> State

    Methods:
    update_lot_produced:

    ORM:
    Crate
    Write
    """
    _inherit = "stock.move.line"

    production_state = fields.Selection(
        related="workorder_id.production_id.state",
        string="MO Status")

    @api.model_create_multi
    def create(self, vals):
        """ORM: Create

        :param vals: Received values in dictionary format
        :return: Recordset of Move Line
        """
        res = super(StockMoveLine, self).create(vals)
        lot_product_ids = list(
            set(res.lot_produced_ids.ids) - set(res.lot_id.lot_ids.ids)
        )
        # Managing Lot Installed Location.
        if lot_product_ids:
            res.lot_id.write({
                'lot_ids': [(4, x) for x in lot_product_ids]
            })
        return res

    def write(self, vals):
        """ORM: Write

        :param vals: Received values in dictionary format
        :return: Boolean or Super Call
        """
        res = False
        quality_check = self.env['quality.check']
        for line in self:
            if 'lot_id' in vals:
                line.lot_id.lot_ids = False
                qc = quality_check.search([
                    ('component_id', '=', self.product_id.id),
                    ('lot_id', '=', self.lot_id.id),
                    ('finished_lot_id', 'in', self.lot_produced_ids.ids),
                ])
                if qc:
                    qc.write({
                        'lot_id': vals['lot_id']
                    })
            if 'lot_id' in vals and self.consume_line_ids:
                self.consume_line_ids.update_lot_produced(
                    self.lot_id.id, vals['lot_id'])
            res = super(StockMoveLine, line).write(vals)
            if 'lot_id' in vals and line.qty_done != 0:
                line.lot_id.lot_ids = [
                    (4, x) for x in line.lot_produced_ids.ids]
            if line.lot_produced_ids and line.qty_done == 0:
                line.lot_id.write({
                    'lot_ids': [(3, x) for x in line.lot_produced_ids.ids]
                })
            if 'consume_line_ids' in vals and \
                    line.product_id.is_serialization_product():
                line.consume_line_ids.mapped('lot_id').write({
                    'lot_ids': [(4, line.lot_id and line.lot_id.id or False)]
                })
        return res

    def update_lot_produced(self, old_produced_lot, new_produced_lot):
        """Replace Lot Produced

        To replace old lot with new lot on moves to unlink the older and its
        installation location.

        :param old_produced_lot: Lot/Serial Number
        :param new_produced_lot: Lot/Serial Number
        :return: None
        """
        self.write({
            'lot_produced_ids': [
                (3, old_produced_lot),
                (4, new_produced_lot)
            ]
        })
