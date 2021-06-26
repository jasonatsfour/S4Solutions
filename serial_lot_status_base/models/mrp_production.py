# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    """ Manufacturing Orders
    To manage installed location on Lot/Serial Number.

    Methods:
    assign_installed_location: New
    post_inventory: Override
    """
    _inherit = 'mrp.production'

    def assign_installed_location(self, moves_to_do):
        """Assign Installed Location
        It will assign finished lot only those moves which is not done yet.
        Manage installed location on component lots
        when posting inventory from MRP.
        :param moves_to_do: MRP Component which is not done/cancel
        :return: True
        """
        for move_line in moves_to_do.mapped("move_line_ids").filtered(
                lambda m: m.lot_id):
            move_line.lot_id.write({
                'lot_ids': [
                    (4, parent_lot.id)
                    for parent_lot in move_line.lot_produced_ids
                ]
            })
        return True

    def post_inventory(self):
        """MO Post Inventory

        Override this method to manage Installed Location.

        Removed User error:
            - At least one work order has a quantity produced lower than the
            quantity produced in the manufacturing order. You must complete
            the work orders before posting the inventory.

        After remove error filtered unfinished moves and assign the data with
        assign_installed_location name function call,
        and rest of flow as mrp base.

        :return: Boolean or Raise Error
        :raise: User Error
        """
        for order in self:
            # Removed User error:
            moves_not_to_do = order.move_raw_ids.filtered(
                lambda x: x.state == 'done')
            moves_to_do = order.move_raw_ids.filtered(
                lambda x: x.state not in ('done', 'cancel'))
            for move in moves_to_do.filtered(
                    lambda m: m.product_qty == 0.0 and m.quantity_done > 0):
                move.product_uom_qty = move.quantity_done
            # MRP do not merge move, catch the result of _action_done in order
            # to get extra moves.

            # Assign installed location to Unfinished moves
            # and then rest of the is same as base.
            order.assign_installed_location(moves_to_do)

            moves_to_do._action_done()
            moves_to_do = order.move_raw_ids.filtered(
                lambda x: x.state == 'done') - moves_not_to_do
            order._cal_price(moves_to_do)
            moves_to_finish = order.move_finished_ids.filtered(
                lambda x: x.state not in ('done', 'cancel'))
            moves_to_finish = moves_to_finish._action_done()
            order.workorder_ids.mapped('raw_workorder_line_ids').unlink()
            # Calling from Odoo/customaddons/manufacturing_traceability_base/models/mrp_workorder.py : 792
            if not self._context.get('no_need_to_finished_lines', False):
                order.workorder_ids.mapped('finished_workorder_line_ids').unlink()
            order.action_assign()
            consume_move_lines = moves_to_do.mapped('move_line_ids')
            for moveline in moves_to_finish.mapped('move_line_ids'):
                # Manage Partial Serialication Product Produce id as well.
                if moveline.move_id.product_id.is_serialization_product() and \
                        moveline.product_id == order.product_id or \
                        moveline.lot_id in consume_move_lines. \
                        mapped('lot_produced_ids'):
                    if any([
                        not ml.lot_produced_ids for ml in consume_move_lines
                    ]):
                        raise UserError(_(
                            'You can not consume without telling'
                            ' for which lot you consumed it'
                        ))
                    # Link all movelines in the consumed with same
                    # lot_produced_ids false or the correct lot_produced_ids
                    filtered_lines = consume_move_lines.filtered(
                        lambda ml: moveline.lot_id in ml.lot_produced_ids)
                    moveline.write({
                        'consume_line_ids': [(6, 0, [
                            x for x in filtered_lines.ids])]
                    })
                else:
                    # Link with everything
                    moveline.write({
                        'consume_line_ids': [(6, 0, [
                            x for x in consume_move_lines.ids])]
                    })
        return True
