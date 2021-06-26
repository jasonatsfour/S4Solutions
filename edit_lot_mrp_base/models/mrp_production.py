# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models


class MrpProduction(models.Model):
    """Inherited: MRP Production.

    Methods:
    button_plan
    button_unplan
    update_wo_with_finished_move
    get_line_to_update
    update_wo_with_component_move
    update_wo_qcp_lot

    ORM:
    write
    """
    _inherit = 'mrp.production'

    def button_plan(self):
        """Inherited: Button Plan to create WO.

        Prepare the moves and link with WO.

        :return: Boolean
        """
        res = super(MrpProduction, self).button_plan()
        self.move_raw_ids._action_assign()
        stock_quant = self.env['stock.quant']
        mv_line = self.env['stock.move.line']
        for move in self.move_raw_ids:
            if move.reserved_availability <= 0:
                move_line_vals_list = []
                forced_package_id = move.package_level_id.package_id or None
                available_quantity = stock_quant._get_available_quantity(
                    move.product_id, move.location_id,
                    package_id=forced_package_id)
                if available_quantity <= 0:
                    move_line_vals_list.append(
                        move._prepare_move_line_vals(quantity=0))
                    mv_line.create(move_line_vals_list)
                if self.workorder_ids:
                    move.move_line_ids.write({
                        'workorder_id': self.workorder_ids[-1]
                    })
        return res

    def button_unplan(self):
        """Inherited: Button Unplanned.

        If any one unplanned the MO then all linked WO moves line will be
        unlinked and delete.

        :return: Super Call returned values
        """
        rec = super(MrpProduction, self).button_unplan()
        stock_quant = self.env['stock.quant']
        for move in self.move_raw_ids:
            if move.reserved_availability <= 0:
                forced_package_id = move.package_level_id.package_id or None
                available_quantity = stock_quant._get_available_quantity(
                    move.product_id, move.location_id,
                    package_id=forced_package_id)
                if available_quantity <= 0:
                    move.move_line_ids = [(5,)]
        return rec

    def write(self, vals):
        """ORM: Write.

        Update the WO finished lot if replace the finished lot on MO or update
        the component lot if replace the lot of Components.

        While update the finished lot of WO pass the wo_finished_lot_done as
        False to avoid the recursive error.

        :param vals: Received values in dictionary format
        :return: Super Call
        """
        if not self.workorder_ids:
            return super(MrpProduction, self).write(vals)
        if 'finished_move_line_ids' in vals and not self._context.get(
                'wo_finished_lot_done', False):
            self.update_wo_with_finished_move(
                vals['finished_move_line_ids']
            )
        elif 'move_raw_ids' in vals:
            self.update_wo_with_component_move(
                vals['move_raw_ids']
            )
        return super(MrpProduction, self).write(vals)

    def update_wo_with_finished_move(self, finished_move_lot):
        """Update WO Finished Lot.

        Update the WO finished lot if finished lot changed.

        :param finished_move_lot: Dictionary of finished move lines
        :return: None
        """
        if 'lot_id' in finished_move_lot[0][2]:
            prev_id = self.finished_move_line_ids.filtered(
                lambda fn: fn.id == finished_move_lot[0][1]
            ).lot_id
            workorders = self.workorder_ids.filtered(
                lambda wo: wo.finished_lot_id == prev_id
            )
            for wo in workorders:
                wo.write({
                    'finished_lot_id': finished_move_lot[0][2]['lot_id']
                })

    def get_line_to_update(self, move):
        """Line to Update.

        To find the index of updated row.

        :param move: Dictionary of update move raw.
        :return: Index for the update move (id)
        """
        index = 0
        for line in move:
            if line[0] != 1:
                index += 1
        return index

    def update_wo_with_component_move(self, move_raw_ids):
        """To update WO with Raw move.

        get the id of the move and update the lot on WO and QCP.

        :param move_raw_ids:
        :return: None
        """
        for move in move_raw_ids:
            # To get the id of update move raw.
            if not move[2] or 'move_line_ids' not in move[2]:
                continue
            index = self.get_line_to_update(move[2]['move_line_ids'])
            if 'lot_id' in move[2]['move_line_ids'][index][2]:
                self.update_wo_qcp_lot(move[2]['move_line_ids'], index)

    def update_wo_qcp_lot(self, move, index=0):
        """Update lot on WO QCP.

        First open the move and get the details of component, finished lot and
        the lot of component to search the QC and update the lot_id to QC.

        :param move: Dictionary of update moves from Vals
        :param index: ID of update move line raw
        :return: None
        """
        move_line = self.env['stock.move.line'].browse(move[index][1])
        qc = self.env['quality.check'].search([
            ('component_id', '=', move_line.product_id.id),
            ('lot_id', '=', move_line.lot_id.id),
            ('finished_lot_id', 'in', move_line.lot_produced_ids.ids),
        ])
        qc.write({
            'lot_id': move[index][2]['lot_id']
        })
