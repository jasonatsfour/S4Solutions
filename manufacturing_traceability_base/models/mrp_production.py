# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models, fields, _, api
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    """Manufacturing Orders

    """
    _inherit = 'mrp.production'

    # what-if? Redefine show_final_lots
    # show_final_lots = fields.Boolean(string='Show Final Lots',
    #                                  compute='_compute_show_lots')
    # what-if? Redefine post_visible
    # post_visible = fields.Boolean(
    #     string='Allowed to Post Inventory', compute='_compute_post_visible',
    #     help='Technical field to check when we can post')

    @api.depends('product_id.tracking', 'product_id.partial_serialization_id')
    def _compute_show_lots(self):
        """

        :return:
        """
        for production in self:
            production.show_final_lots = production.product_id. \
                is_serialization_product()

    @api.depends('move_raw_ids.quantity_done',
                 'move_finished_ids.quantity_done', 'is_locked')
    def _compute_post_visible(self):
        """

        :return:
        """
        for order in self:
            moves = order.move_finished_ids
            if order.product_tmpl_id._is_cost_method_standard():
                moves |= order.move_raw_ids
            order.post_visible = order.is_locked and any(
                (x.quantity_done > 0 and x.state not in ['done', 'cancel'])
                for x in moves
            )
            order.post_visible &= all(
                wo.state in ['done', 'cancel'] for wo in order.workorder_ids
            ) or all(
                not m.product_id.is_serialization_product()
                for m in order.move_raw_ids
            )

    def _workorders_create(self, bom, bom_data):
        """

        :param bom: In case of recursive.
        :param bom_data: Could create work orders for child BoMs.
        :return:
        """
        workorders = self.env['mrp.workorder']

        # Initial qty producing
        quantity = max(self.product_qty - sum(self.move_finished_ids.filtered(
            lambda move: move.product_id == self.product_id
        ).mapped('quantity_done')), 0)
        quantity = self.product_id.uom_id._compute_quantity(
            quantity, self.product_uom_id)
        if self.product_id.is_serial_product():
            quantity = 1.0

        for operation in bom.routing_id.operation_ids:
            workorder = workorders.create({
                'name': operation.name,
                'production_id': self.id,
                'workcenter_id': operation.workcenter_id.id,
                'product_uom_id': self.product_id.uom_id.id,
                'operation_id': operation.id,
                'state': len(workorders) == 0 and 'ready' or 'pending',
                'qty_producing': quantity,
                'consumption': self.bom_id.consumption,
            })
            if workorders:
                workorders[-1].next_work_order_id = workorder.id
                workorders[-1]._start_nextworkorder()
            workorders += workorder

            moves_raw = self.move_raw_ids.filtered(
                lambda move: move.operation_id == operation and
                move.bom_line_id.bom_id.routing_id == bom.routing_id)
            moves_finished = self.move_finished_ids.filtered(
                lambda move: move.operation_id == operation)

            # - Raw moves from a BoM where a routing was set but no operation
            # was precised should be consumed at the
            # last workorder of the linked routing.
            # - Raw moves from a BoM where no rounting was set should be
            # consumed at the last workorder of the main routing.
            if len(workorders) == len(bom.routing_id.operation_ids):
                moves_raw |= self.move_raw_ids.filtered(
                    lambda move: not move.operation_id and
                    move.bom_line_id.bom_id.routing_id == bom.routing_id)
                moves_raw |= self.move_raw_ids.filtered(
                    lambda move: not move.workorder_id and not
                    move.bom_line_id.bom_id.routing_id)
                moves_finished |= self.move_finished_ids.filtered(
                    lambda move: move.product_id != self.product_id and not
                    move.operation_id)

            moves_raw.mapped('move_line_ids').write({
                'workorder_id': workorder.id
            })

            (moves_finished | moves_raw).write({'workorder_id': workorder.id})
            workorder._generate_wo_lines()
        return workorders

    def _check_lots(self):
        """

        :return: None or Raise Error
        :raise: User Error
        """
        # Check that the components were consumed
        # for lots that we have produced.
        if self.product_id.is_serialization_product():
            finished_lots = self.finished_move_line_ids.mapped('lot_id')
            raw_finished_lots = self.move_raw_ids.mapped(
                'move_line_ids.lot_produced_ids')
            lots_short = raw_finished_lots - finished_lots
            if lots_short:
                err_msg = _(
                    'Some components have been consumed for a lot/serial '
                    'number that has not been produced. '
                    'Unlock the MO and click on the components lines to '
                    'correct it.\n'
                    'List of the components:\n'
                )
                lines = self.move_raw_ids.mapped('move_line_ids').filtered(
                    lambda line: lots_short & line.lot_produced_ids)
                for ml in lines:
                    err_msg += "%s (%s)\n" % (
                        ml.product_id.display_name,
                        ', '.join(
                            (lots_short & ml.lot_produced_ids).mapped('name'))
                    )
                raise UserError(err_msg)
