# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models, fields, _
from odoo.exceptions import UserError


class MrpProductProduce(models.TransientModel):
    """

    """
    _inherit = 'mrp.product.produce'

    partial_serialization_id = fields.Many2one(
        related="product_id.partial_serialization_id", store=True)
    partial_serialization_type = fields.Selection(
        related="product_id.partial_serialization_id.traceability_type",
        string="Product tracking", readonly=True, store=True)

    def _update_finished_move(self):
        """

        :return: Super return or Raise Error
        :raise: User Error
        """
        production_move = self.production_id.move_finished_ids.filtered(
            lambda move: move.product_id == self.product_id and
                         move.state not in ('done', 'cancel')
        )
        product_id = production_move.product_id
        trace_type = product_id.partial_serialization_id.traceability_type
        if production_move and trace_type:
            if not self.finished_lot_id:
                raise UserError(_(
                    'You need to provide a lot for the finished product.'))
            move_line = production_move.move_line_ids.filtered(
                lambda line: line.lot_id.id == self.finished_lot_id.id
            )
            if move_line:
                if self.product_id.is_serial_product():
                    raise UserError(_(
                        'You cannot produce the same serial number twice.'))
                move_line.product_uom_qty += self.qty_producing
                move_line.qty_done += self.qty_producing
            else:
                location_dest_id = production_move.location_dest_id
                location_dest_id = location_dest_id._get_putaway_strategy(
                    self.product_id).id or production_move.location_dest_id.id
                move_line.create({
                    'move_id': production_move.id,
                    'product_id': production_move.product_id.id,
                    'lot_id': self.finished_lot_id.id,
                    'product_uom_qty': self.qty_producing,
                    'product_uom_id': self.product_uom_id.id,
                    'qty_done': self.qty_producing,
                    'location_id': production_move.location_id.id,
                    'location_dest_id': location_dest_id,
                })
        else:
            return super(MrpProductProduce, self)._update_finished_move()


class MrpProductProduceLine(models.TransientModel):
    """

    """
    _inherit = 'mrp.product.produce.line'

    partial_serialization_id = fields.Many2one(
        related="product_id.partial_serialization_id", store=True)
    partial_serialization_type = fields.Selection(
        related="product_id.partial_serialization_id.traceability_type",
        string="Product tracking", readonly=True, store=True)
    lot_id = fields.Many2one(
        'stock.production.lot', 'Lot/Serial Number',
        check_company=True,
        domain="[('product_id', '=', product_id),"
               "('is_none_production', '=', False),"
               "('stock_production_lot_status_id.name', '!=', 'Installed'),"
               "'|', ('company_id', '=', False),"
               "('company_id', '=', company_id)]")

    def _update_move_lines(self):
        """

        :return: Super return or Raise Error
        :raise: User Error
        """
        if self.partial_serialization_id and not self.lot_id:
            raise UserError(_(
                'Please enter a lot or serial number for %s !'
            ) % self.product_id.display_name)
        if self.lot_id and self.product_id.is_serial_product() and \
                self.lot_id in self.move_id.move_line_ids.filtered(
            lambda ml: ml.qty_done
        ).mapped('lot_id'):
            raise UserError(_(
                'You cannot consume the same serial number twice.'
                'Please correct the serial numbers encoded.'))
        return super(MrpProductProduceLine, self)._update_move_lines()
