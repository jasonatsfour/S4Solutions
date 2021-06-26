# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from itertools import groupby
from operator import itemgetter
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero
import logging

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    """

    """
    _inherit = 'stock.move'

    needs_lots = fields.Boolean('Tracking', compute='_compute_needs_lots')
    workorder_state = fields.Selection(related="workorder_id.state", store=True)
    reference_move_of_original_component_id = fields.Many2one('stock.move', string="Original MO's component move")
    externally_added_component = fields.Boolean(string="Is Externally Added on MO?")

    def button_delete_operation(self):
        # Check the current model and quantity done >0 , also we checked "checked_condition" ,
        # it will make sure that it is not coming from wizard it self.
        if self.filtered(lambda m: m.quantity_done > 0 and (m.raw_material_production_id or m.production_id)):
            return {
                'name': 'Confirmation',
                'type': 'ir.actions.act_window',
                'res_model': 'message.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_name': 'This component has already been consumed by at least '
                                            'one Finished Product on this Manufacturing Order.'
                                            ' If you continue, that consumption transaction will be reversed and '
                                            'it will no longer appear on the As-Built traceability for any'
                                            ' Finished Products on this Manufacturing Order. '
                                            'Do you want to continue?', 'default_stock_move_ids': [(6, 0, self.ids)]}
            }
        else:
            production_id = self.raw_material_production_id or self.production_id
            self._do_unreserve()
            production_id.reset_workorders(product_ids=self.mapped('product_id').ids)
            self.write({'state': 'draft'})
            self.unlink()

    def reverse_moves(self, move_vals, reference):
        reversed_moves = self.env['stock.move']
        for move_id in self:
            move_vals.update({
                'name': 'Reversed Move' + ' - %s' % reference if reference else '',
                'location_id': move_id.location_dest_id.id,
                'location_dest_id': move_id.location_id.id,
                'reference': reference,
            })
            reversed_move_id = move_id.copy(move_vals)
            reversed_move_id._action_assign()
            reversed_move_id._set_quantity_done(move_id.quantity_done)
            reversed_move_id._action_done()
            reversed_moves |= reversed_move_id
        return reversed_moves

    def action_reverse_moves(self, for_mo=False, reference=False):
        if self.filtered(lambda sm: sm.state != 'done'):
            _logger.warning("You have uncompleted moves, that can not be reversed.")
            return True
        move_vals = {'raw_material_production_id': False, 'production_id': False,
                     'picking_type_id': False, 'picking_id': False} if for_mo else {}
        # Ability to cancel moves from mo only
        self.reverse_moves(move_vals, reference)
        production_id = self.raw_material_production_id or self.production_id
        self.write({
            'state': 'draft',
            'raw_material_production_id': False,
            'production_id': False,
        })
        self._action_cancel()
        production_id.reset_workorders(product_ids=self.mapped('product_id'))

    @api.model
    def create(self, vals):
        stock_move = super(StockMove, self).create(vals)
        if stock_move.raw_material_production_id and stock_move.raw_material_production_id.workorder_ids\
                and stock_move.externally_added_component:
            workorder = stock_move.raw_material_production_id.workorder_ids.filtered(
                lambda wo: wo.operation_id == stock_move.operation_id)\
                        or stock_move.raw_material_production_id.workorder_ids[-1]
            stock_move.workorder_id = workorder[0].id
            workorder.generate_wo_lines_for_specific_move(moves=stock_move)
            workorder.with_context(move_raw_ids=stock_move, move_finished_ids=self.env['stock.move'])._create_checks()
        return stock_move

    def write(self, vals):
        if 'operation_id' in vals:
            operation_id = vals['operation_id']
            self.raw_material_production_id.button_update_wo(self, operation_id)
        return super(StockMove, self).write(vals)

    @api.depends('product_id.tracking')
    def _compute_needs_lots(self):
        """

        :return:
        """
        for move in self:
            move.needs_lots = move.product_id.is_serialization_product()

    def _update_reserved_quantity(self, need, available_quantity, location_id,
                                  lot_id=None, package_id=None,
                                  owner_id=None, strict=True):
        """

        :param need:
        :param available_quantity:
        :param location_id:
        :param lot_id:
        :param package_id:
        :param owner_id:
        :param strict:
        :return:
        """
        self.ensure_one()
        if not lot_id:
            lot_id = self.env['stock.production.lot']
        if not package_id:
            package_id = self.env['stock.quant.package']
        if not owner_id:
            owner_id = self.env['res.partner']
        taken_quantity = min(available_quantity, need)
        if not strict:
            taken_quantity_move_uom = self.product_id.uom_id \
                ._compute_quantity(taken_quantity,
                                   self.product_uom, rounding_method='DOWN')
            taken_quantity = self.product_uom \
                ._compute_quantity(taken_quantity_move_uom,
                                   self.product_id.uom_id,
                                   rounding_method='HALF-UP')
        quants = []
        partial_serial = self.product_id.partial_serialization_id
        if self.product_id.tracking == 'serial' or (
                partial_serial and
                partial_serial.traceability_type == 'serial'):
            rounding = self.env['decimal.precision'].precision_get(
                'Product Unit of Measure')
            if float_compare(taken_quantity, int(taken_quantity),
                             precision_digits=rounding) != 0:
                taken_quantity = 0
        try:
            if not float_is_zero(
                    taken_quantity,
                    precision_rounding=self.product_id.uom_id.rounding):
                quants = self.env['stock.quant']._update_reserved_quantity(
                    self.product_id, location_id, taken_quantity,
                    lot_id=lot_id, package_id=package_id,
                    owner_id=owner_id, strict=strict)
        except UserError:
            taken_quantity = 0
        # Find a candidate move line to update or create a new one.
        for reserved_quant, quantity in quants:
            to_update = self.move_line_ids.filtered(
                lambda ml: ml._reservation_is_updatable(
                    quantity, reserved_quant))
            if to_update:
                to_update[0].with_context(
                    bypass_reservation_update=True
                ).product_uom_qty += self.product_id.uom_id._compute_quantity(
                    quantity, to_update[0].product_uom_id,
                    rounding_method='HALF-UP')
            else:
                mv_line_env = self.env['stock.move.line']
                if self.product_id.tracking == 'serial' or (
                        partial_serial and
                        partial_serial.traceability_type == 'serial'):
                    for i in range(0, int(quantity)):
                        mv_line_env.create(
                            self._prepare_move_line_vals(
                                quantity=1, reserved_quant=reserved_quant))
                else:
                    mv_line_env.create(
                        self._prepare_move_line_vals(
                            quantity=quantity, reserved_quant=reserved_quant))
        return taken_quantity

    def _action_assign(self):
        """
        Reserve stock moves by creating their stock move lines.
        A stock move is considered reserved once the sum of `product_qty`
        for all its move lines is equal to its `product_qty`.
        If it is less, the stock move is considered partially available.
        :return:
        """
        assigned_moves = self.env['stock.move']
        partially_available_moves = self.env['stock.move']
        # Read the `reserved_availability` field of the moves out of
        # the loop to prevent unwanted
        # cache invalidation when actually reserving the move.
        rsrv_availability = {
            move: move.reserved_availability for move in self
        }
        roundings = {
            move: move.product_id.uom_id.rounding for move in self
        }
        move_line_vals_list = []
        for move in self.filtered(
                lambda m: m.state in [
                    'confirmed', 'waiting', 'partially_available']):
            rounding = roundings[move]
            miss_rsrv_uom_qty = move.product_uom_qty - rsrv_availability[move]
            missing_reserved_quantity = move.product_uom._compute_quantity(
                miss_rsrv_uom_qty, move.product_id.uom_id,
                rounding_method='HALF-UP')
            if move._should_bypass_reservation():
                # create the move line(s) but do not impact quants
                if move.product_id.tracking == 'serial' or (
                        move.product_id.partial_serialization_id and
                        move.product_id.partial_serialization_id
                                .traceability_type == 'serial') and (
                        move.picking_type_id.use_create_lots or
                        move.picking_type_id.use_existing_lots):
                    for i in range(0, int(missing_reserved_quantity)):
                        move_line_vals_list.append(
                            move._prepare_move_line_vals(quantity=1))
                else:
                    to_update = move.move_line_ids.filtered(
                        lambda ml:
                        ml.product_uom_id == move.product_uom and
                        ml.location_id == move.location_id and
                        ml.location_dest_id == move.location_dest_id and
                        ml.picking_id == move.picking_id and
                        not ml.lot_id and
                        not ml.package_id and
                        not ml.owner_id)
                    if to_update:
                        to_update[0].product_uom_qty += miss_rsrv_uom_qty
                    else:
                        move_line_vals_list.append(
                            move._prepare_move_line_vals(
                                quantity=missing_reserved_quantity))
                assigned_moves |= move
            else:
                if float_is_zero(
                        move.product_uom_qty,
                        precision_rounding=move.product_uom.rounding):
                    assigned_moves |= move
                elif not move.move_orig_ids:
                    if move.procure_method == 'make_to_order':
                        continue
                    # If we don't need any quantity,
                    # consider the move assigned.
                    need = missing_reserved_quantity
                    if float_is_zero(need, precision_rounding=rounding):
                        assigned_moves |= move
                        continue
                    # Reserve new quants and create move lines accordingly.
                    forced_package_id = move.package_level_id.package_id or \
                                        None
                    available_quantity = self.env['stock.quant'] \
                        ._get_available_quantity(
                        move.product_id, move.location_id,
                        package_id=forced_package_id)
                    if available_quantity <= 0:
                        continue
                    taken_quantity = move._update_reserved_quantity(
                        need, available_quantity, move.location_id,
                        package_id=forced_package_id, strict=False)
                    if float_is_zero(taken_quantity,
                                     precision_rounding=rounding):
                        continue
                    if float_compare(need, taken_quantity,
                                     precision_rounding=rounding) == 0:
                        assigned_moves |= move
                    else:
                        partially_available_moves |= move
                else:
                    # Check what our parents brought and what our siblings
                    # took in order to determine what we can distribute.
                    # `qty_done` is in `ml.product_uom_id` and,
                    # as we will later increase
                    # the reserved quantity on the quants, convert it here in
                    # `product_id.uom_id`
                    # (the UOM of the quants is the UOM of the product).
                    move_lines_in = move.move_orig_ids.filtered(
                        lambda m: m.state == 'done'
                    ).mapped('move_line_ids')
                    keys_in_groupby = ['location_dest_id', 'lot_id',
                                       'result_package_id', 'owner_id']

                    def _keys_in_sorted(ml):
                        return (ml.location_dest_id.id, ml.lot_id.id,
                                ml.result_package_id.id, ml.owner_id.id)

                    grouped_move_lines_in = {}
                    for k, g in groupby(
                            sorted(move_lines_in, key=_keys_in_sorted),
                            key=itemgetter(*keys_in_groupby)):
                        qty_done = 0
                        for ml in g:
                            qty_done += ml.product_uom_id._compute_quantity(
                                ml.qty_done, ml.product_id.uom_id)
                        grouped_move_lines_in[k] = qty_done
                    move_lines_out_done = (
                            move.move_orig_ids
                            .mapped('move_dest_ids') - move) \
                        .filtered(lambda m: m.state in ['done']) \
                        .mapped('move_line_ids')
                    # As we defer the write on the stock.move's state at
                    # the end of the loop, there could be moves to consider
                    # in what our siblings already took.
                    moves_out_siblings = move.move_orig_ids.mapped(
                        'move_dest_ids') - move
                    moves_out_siblings_to_consider = moves_out_siblings & (
                            assigned_moves + partially_available_moves)
                    reserved_moves_out_siblings = moves_out_siblings.filtered(
                        lambda m: m.state in [
                            'partially_available', 'assigned'])
                    move_lines_out_reserved = (
                            reserved_moves_out_siblings |
                            moves_out_siblings_to_consider
                    ).mapped('move_line_ids')
                    keys_out_groupby = ['location_id', 'lot_id',
                                        'package_id', 'owner_id']

                    def _keys_out_sorted(ml):
                        return (ml.location_id.id, ml.lot_id.id,
                                ml.package_id.id, ml.owner_id.id)

                    grouped_move_lines_out = {}
                    for k, g in groupby(sorted(move_lines_out_done,
                                               key=_keys_out_sorted),
                                        key=itemgetter(*keys_out_groupby)):
                        qty_done = 0
                        for ml in g:
                            qty_done += ml.product_uom_id._compute_quantity(
                                ml.qty_done, ml.product_id.uom_id)
                        grouped_move_lines_out[k] = qty_done
                    for k, g in groupby(sorted(move_lines_out_reserved,
                                               key=_keys_out_sorted),
                                        key=itemgetter(*keys_out_groupby)):
                        grouped_move_lines_out[k] = sum(
                            self.env['stock.move.line'].concat(
                                *list(g)).mapped('product_qty'))
                    available_move_lines = {
                        key: grouped_move_lines_in[key] -
                             grouped_move_lines_out.get(key, 0)
                        for key in grouped_move_lines_in.keys()
                    }
                    # pop key if the quantity available amount to 0
                    available_move_lines = dict(
                        (k, v) for k, v in available_move_lines.items() if v)

                    if not available_move_lines:
                        continue
                    for move_line in move.move_line_ids.filtered(
                            lambda m: m.product_qty):
                        if available_move_lines.get((
                                move_line.location_id,
                                move_line.lot_id,
                                move_line.result_package_id,
                                move_line.owner_id)):
                            available_move_lines[(
                                move_line.location_id,
                                move_line.lot_id,
                                move_line.result_package_id,
                                move_line.owner_id
                            )] -= move_line.product_qty
                    for (location_id, lot_id, package_id, owner_id), \
                        quantity in available_move_lines.items():
                        need = move.product_qty - sum(
                            move.move_line_ids.mapped('product_qty'))
                        available_quantity = self.env['stock.quant'] \
                            ._get_available_quantity(
                            move.product_id, location_id, lot_id=lot_id,
                            package_id=package_id, owner_id=owner_id,
                            strict=True)
                        if float_is_zero(available_quantity,
                                         precision_rounding=rounding):
                            continue
                        taken_quantity = move._update_reserved_quantity(
                            need, min(quantity, available_quantity),
                            location_id, lot_id, package_id, owner_id)
                        if float_is_zero(taken_quantity,
                                         precision_rounding=rounding):
                            continue
                        if float_is_zero(need - taken_quantity,
                                         precision_rounding=rounding):
                            assigned_moves |= move
                            break
                        partially_available_moves |= move
            if move.product_id.tracking == 'serial' or (
                    move.product_id.partial_serialization_id and
                    move.product_id.partial_serialization_id.
                            traceability_type == 'serial'):
                move.next_serial_count = move.product_uom_qty

        self.env['stock.move.line'].create(move_line_vals_list)
        partially_available_moves.write({
            'state': 'partially_available'
        })
        assigned_moves.write({
            'state': 'assigned'
        })
        self.mapped('picking_id')._check_entire_pack()

