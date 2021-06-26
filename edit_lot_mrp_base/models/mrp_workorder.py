# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, _
from odoo.exceptions import UserError


class MrpWorkorder(models.Model):
    """Inherited: MRP Workorder to allow user to edit the lot on done WO.

    ORM:
    write
    """
    _inherit = 'mrp.workorder'

    edit_move_line_ids = fields.One2many(
        'stock.move.line', 'workorder_id', string='Moves To Edit',
        domain=[('lot_id', '!=', False), ('qty_done', '!=', 0)],
        help="Inventory moves for which you must scan a lot number at this work order")

    def write(self, values):
        """ORM: Write

        Override this method to manage Lot/Serial even after Finished WO.
        At the end of the process it check if any changes hase made in
        finished_workorder_line_ids and if it is lot then it must update in QCP
        either finished lot or component lot.

        A flag named wo_finished_lot_done pass in context while writing
        the finished move line to avoid the recursive depth error.

        Super method call with Model class To ignore an error.
        Here, Ignore error: 'You can not change the finished work order.'

        :param values: Received values in dictionary format
        :return: None or Raise Error
        :raise: User Error
        """
        if 'production_id' in values:
            raise UserError(_(
                'You cannot link this work order '
                'to another manufacturing order.'
            ))
        if 'workcenter_id' in values:
            mrp_wc = self.env['mrp.workcenter']
            for workorder in self:
                if workorder.workcenter_id.id != values['workcenter_id']:
                    if workorder.state in ('progress', 'done', 'cancel'):
                        raise UserError(_(
                            'You cannot change the workcenter of a '
                            'work order that is in progress or done.'))
                    workorder.leave_id.resource_id = mrp_wc.browse(
                        values['workcenter_id']).resource_id
        # No need to this warning
        # if list(values.keys()) != ['time_ids'] and any(
        # workorder.state == 'done' for workorder in self):
        #     raise UserError(_(
        #     'You can not change the finished work order.'))
        if 'date_planned_start' in values \
                or 'date_planned_finished' in values:
            for workorder in self:
                start_date = fields.Datetime.to_datetime(
                    values.get('date_planned_start')
                ) or workorder.date_planned_start
                end_date = fields.Datetime.to_datetime(values.get(
                    'date_planned_finished'
                )) or workorder.date_planned_finished
                if start_date and end_date and start_date > end_date:
                    raise UserError(_(
                        'The planned end date of the work order cannot '
                        'be prior to the planned start date, please '
                        'correct this to save the work order.'))
                # Update MO dates if the start date of the first WO or the
                # finished date of the last WO is update.
                if workorder == workorder.production_id.workorder_ids[0] and \
                        'date_planned_start' in values:
                    workorder.production_id.with_context(
                        force_date=True
                    ).write({
                        'date_planned_start': fields.Datetime.to_datetime(
                            values['date_planned_start'])
                    })
                if workorder == workorder.production_id.workorder_ids[-1] and \
                        'date_planned_finished' in values:
                    workorder.production_id.with_context(
                        force_date=True
                    ).write({
                        'date_planned_finished': fields.Datetime.to_datetime(
                            values['date_planned_finished'])
                    })
        if 'finished_workorder_line_ids' in values:
            # TO update the finished lot for finished WO.
            values.update({
                'finished_lot_id': values[
                    'finished_workorder_line_ids'][0][2]['lot_id']
            })
            finished_wol = self.finished_workorder_line_ids.filtered(
                lambda l: l.id == values['finished_workorder_line_ids'][0][1]
            )
            self.production_id.finished_move_line_ids.filtered(
                lambda l: l.lot_id == finished_wol.lot_id
            ).with_context({'wo_finished_lot_done': True}).write({
                'lot_id': values[
                    'finished_workorder_line_ids'][0][2]['lot_id']
            })
            self.production_id.move_raw_ids.mapped('move_line_ids').filtered(
                lambda l: finished_wol.lot_id in l.lot_produced_ids
            ).with_context({
                'wo_finished_lot_done': True
            }).update_lot_produced(finished_wol.lot_id.id, values[
                'finished_workorder_line_ids'][0][2]['lot_id'])
        if 'finished_lot_id' in values:
            self.check_ids.write({
                'finished_lot_id': values['finished_lot_id']
            })
        # Called directly model super method
        # and avoid MRP method to skip warning
        return super(models.Model, self).write(values)

    def do_finish(self):
        """Inherited: WO - Mark As Done

        :return: Base Call
        """
        rec = super(MrpWorkorder, self).do_finish()
        for res in self:
            res.production_id.move_raw_ids.mapped('move_line_ids').filtered(
                lambda ml: res.finished_lot_id in ml.lot_produced_ids
            ).write({
                'workorder_id': res.id
            })
        return rec