from collections import defaultdict

from odoo import models, fields, _, api
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round


class MrpAbstractWorkorder(models.AbstractModel):
    _inherit = "mrp.abstract.workorder"

    def _update_moves(self):
        """ Once the production is done. Modify the workorder lines into
        stock move line with the registered lot and quantity done.
        """
        # Before writting produce quantities, we ensure they respect the bom strictness
        self._strict_consumption_check()
        vals_list = []
        workorder_lines_to_process = self._workorder_line_ids().filtered(
            lambda line: line.product_id != self.product_id and line.qty_done > 0)
        for line in workorder_lines_to_process:
            line._update_move_lines()
            if float_compare(line.qty_done, 0, precision_rounding=line.product_uom_id.rounding) > 0:
                vals_list += line._create_extra_move_lines()

        self._workorder_line_ids().filtered(lambda line: line.product_id != self.product_id).unlink()
        move_lines = self.env['stock.move.line'].create(vals_list)
        for move_line in move_lines:
            move_line.lot_id.calculate_lot_status(location_id=move_line.location_dest_id.id, operation_type='add')


class MrpProductionWorkcenterLine(models.Model):
    """

    """
    _inherit = 'mrp.workorder'
    _order = 'sequence'

    partial_serialization_id = fields.Many2one(
        related="product_id.partial_serialization_id",
        string="Partial serialization", store=True)
    partial_serialization_type = fields.Selection(
        related="product_id.partial_serialization_id.traceability_type",
        string="Product tracking", readonly=True, store=True)
    component_partial_serialization_id = fields.Many2one(
        related="component_id.partial_serialization_id",
        string="component Partial serialization", store=True)
    component_partial_tracking = fields.Selection(
        related='component_id.partial_serialization_id.traceability_type',
        string="Is Component Partial Tracked?", readonly=False)
    finished_lot_id = fields.Many2one(
        'stock.production.lot', 'Lot/Serial Number',
        domain="[('id', 'in', allowed_lots_domain),"
               "('stock_production_lot_status_id.key', '=', "
               "'available')]",
        states={
            'done': [('readonly', True)],
            'cancel': [('readonly', True)]
        }, check_company=True)
    backflush_on_mo_completion = fields.Boolean(
        string="Backflush on WO Completion",
        related="production_id.picking_type_id.backflush_on_mo_completion", store=True)
    splits_allowed = fields.Boolean(string="Splits Allowed",
                                    related="production_id.picking_type_id.splits_allowed", store=True)

    operation_edit_allowed = fields.Boolean(string="Operation Edits Allowed",
                                            related="production_id.picking_type_id.operation_edit_allowed",
                                            store=True)
    sequence = fields.Integer(string='Sequence')
    previous_workorder_id = fields.Many2one('mrp.workorder', string="Previous Workorder")
    picking_type_id = fields.Many2one('stock.picking.type', related="production_id.picking_type_id", store=True)

    def create_re_testable_check(self):
        re_testable_qcp = self.current_quality_check_id.copy({
            'name': self.current_quality_check_id.name + ' (Re-Test)',
            'quality_state': 'none',
            'user_id': False,
            'control_date': False,
            'workorder_id': self.id,
            'point_id': self.current_quality_check_id.point_id.id,
        })
        self.current_quality_check_id.do_fail()
        self.write({'current_quality_check_id': re_testable_qcp.id})
        return {'type': 'ir.actions.act_window_close'}

    def generate_wo_lines_for_specific_move(self, moves):
        for workorder in self:
            """ Generate workorder line for specific moves or update wo lines as per product"""
            move_ids = moves or (workorder.move_raw_ids | workorder.move_finished_ids).filtered(
                lambda move: move.state not in ('done', 'cancel')
            )
            for move in move_ids:
                qty_to_consume = workorder._prepare_component_quantity(move, workorder.qty_producing)
                existing_wo_line = workorder.raw_workorder_line_ids.filtered(
                    lambda wl: wl.product_id == move.product_id)
                if existing_wo_line:
                    existing_wo_line.write({'qty_to_consume': existing_wo_line.qty_to_consume + qty_to_consume})
                else:
                    line_values = workorder._generate_lines_values(move, qty_to_consume)
                    self.env['mrp.workorder.line'].create(line_values)
            remaining_wls = workorder.raw_workorder_line_ids.filtered(lambda wl: wl.qty_to_consume > wl.qty_done)
            workorder.write({'workorder_line_id': remaining_wls[0].id if remaining_wls else False})

    def advance_failure_popup_screen(self):
        action = self.env.ref('manufacturing_traceability_base.action_advance_failure_popup_wizard').read()[0]
        action['context'] = {'default_workorder_id': self.id}
        return action

    def manage_workorder_state(self):
        self[-1].next_work_order_id.state = 'ready'
        return True

    def delete_selected_work_order(self):
        last_wo_id = self[0].production_id.workorder_ids.filtered(lambda wo: not wo.next_work_order_id)
        for workorder in self:
            for move_raw in workorder.mapped('move_raw_ids'):
                transferred_move_raw_id = move_raw.copy({
                    'workorder_id': last_wo_id.id,
                    'reference': last_wo_id.production_id.name,
                })
                move_raw.write({
                    'production_id': False,
                    'raw_material_production_id': False,
                })
                transferred_move_raw_id._action_confirm()
                # transferred_move_raw_id._action_assign()
            for check_id in workorder.check_ids.filtered(lambda c: not c.point_id):
                check_id.copy({
                    'workorder_id': last_wo_id.id,
                })
        last_wo_id._refresh_wo_lines()
        for workorder_line in last_wo_id.raw_workorder_line_ids:
            last_wo_id.check_ids.filtered(lambda c: workorder_line.product_id.id == c.component_id.id).write({
                'workorder_line_id': workorder_line.id,
            })
        self.manage_workorder_state()
        # Delete Selected work orders
        self.unlink()
        wo_list_action = last_wo_id.production_id.action_mrp_workorder_production_specific()
        wo_list_action['domain'] = [('production_id', '=', last_wo_id.production_id.id)]
        return wo_list_action, False

    def check_wo_for_consumption(self, default_context):
        need_to_return_warning = False
        if any([True for state in self.mapped('state') if state in ["progress", "done"]]):
            default_context.update({
                'default_name':
                    'Components have already been consumed against this Work Order.'
                    ' These will be reassigned to the final Work Order of this Manufacturing Order [{0}]'
                    ' if you continue. Do you wish to proceed?'.format(self[0].production_id.name),
                'default_condition_name': 'progress_condition_checked'
            })
            need_to_return_warning = True
        return need_to_return_warning, default_context

    def check_quality_checks(self, check_ids_condition_checked, default_context, action_name):
        need_to_return_warning = False
        if not check_ids_condition_checked:
            if 'none' in self.mapped('check_ids').filtered(lambda c: c.point_id).mapped('quality_state'):
                default_context.update({
                    'default_name':
                        'One or more  uncompleted Quality Checks exist. If you continue,'
                        ' they will not be automatically assigned to a new work order'
                        ' and you will not be able to execute them on this Manufacturing Order [{0}]'
                        ' without recreating them on another Work order manually.'
                        ' Do you wish to continue?'.format(self[0].production_id.name),
                    'default_condition_name': 'check_ids_condition_checked',
                })
                action_name = "Quality Checks Found !!"
                need_to_return_warning = True
        return action_name, need_to_return_warning, default_context

    def checking_preconditions_for_deleting_work_orders(self,
                                                        progress_condition_checked=False,
                                                        check_ids_condition_checked=False):
        if not self:
            return False, False
        last_workorder = False
        last_wo_id = self[0].production_id.workorder_ids.filtered(lambda wo: not wo.next_work_order_id)
        if last_wo_id.id in self.ids:
            last_workorder = True
            return last_wo_id, last_workorder

        if self.mapped('finished_workorder_line_ids'):
            raise UserError("This Work Order has had activity registered against it. It cannot be deleted. "
                            "You may instead Cancel it which will remove its remaining work content from this"
                            " Manufacturing Order.")
        default_context = {'default_workorder_ids': [(6, 0, self.ids)]}
        action_name = "Consumption Found on the workorder!!"
        need_to_return_warning = False
        if not progress_condition_checked:
            need_to_return_warning, default_context = self.check_wo_for_consumption(default_context)
            if not need_to_return_warning:
                action_name, need_to_return_warning, default_context = self.check_quality_checks(
                    check_ids_condition_checked, default_context, action_name)
        else:
            action_name, need_to_return_warning, default_context = self.check_quality_checks(
                check_ids_condition_checked, default_context, action_name)
        if need_to_return_warning:
            return {
                   'name': action_name,
                   'type': 'ir.actions.act_window',
                   'res_model': 'message.wizard',
                   'view_mode': 'form',
                   'view_type': 'form',
                   'target': 'new',
                   'context': default_context,
               }, last_workorder
        else:
            wo_list_action, _ = self.delete_selected_work_order()
            return wo_list_action, last_workorder

    def button_cancel_workorder(self):
        for rec in self:
            rec.with_context(force_delete=True).action_cancel()
            rec.manage_workorder_state()

    def button_delete_workorder(self):
        last_wo_id, last_workorder = self.checking_preconditions_for_deleting_work_orders()
        if 'res_model' in last_wo_id:
            return last_wo_id
        if last_workorder:
            raise UserError("You can not delete last workorder of MO {0}".format(self[0].production_id.name))
        return True

    def do_fail(self):
        self.ensure_one()
        advance_failure_popup = self.env.user.company_id.advance_quality_failure
        if advance_failure_popup:
            return self.advance_failure_popup_screen()
        self.current_quality_check_id.do_fail()
        return self.action_next()

    @api.model
    def _prepare_component_quantity(self, move, qty_producing):
        """Prepare Component Quantity.

        Helper that computes the quantity to consume or to create in case of
        the byproduct, that depending on the quantity producing and the move's
        unit factor.

        :param move: Stock Moves
        :param qty_producing: Float
        :return: Float
        """
        if move.product_id.is_serial_product():
            uom = move.product_id.uom_id
        else:
            uom = move.product_uom
        return move.product_uom._compute_quantity(
            qty_producing * move.unit_factor, uom, round=False)

    def _update_workorder_lines(self):
        """ Update workorder lines.

        According to the new qty currently produced.
        It returns a dict with line to create, update or delete.
        It do not directly write or unlink the line because this function is
        used in onchange and request that write on db
        (e.g. workorder creation).

        :return: List of Dictionary

        """
        line_values = {'to_create': [], 'to_delete': [], 'to_update': {}}
        # moves are actual records
        move_finished_ids = self.move_finished_ids._origin.filtered(
            lambda move: move.product_id != self.product_id and
                         move.state not in ('done', 'cancel'))
        move_raw_ids = self.move_raw_ids._origin.filtered(
            lambda move: move.state not in ('done', 'cancel'))
        for move in move_raw_ids | move_finished_ids:
            move_workorder_lines = self._workorder_line_ids().filtered(
                lambda w: w.move_id == move)

            # Compute the new quantity for the current component
            rounding = move.product_uom.rounding
            new_qty = self._prepare_component_quantity(
                move, self.qty_producing)

            # In case the production uom is different than the workorder uom
            # it means the product is serial and
            # production uom is not the reference
            new_qty = self.product_uom_id._compute_quantity(
                new_qty,
                self.production_id.product_uom_id,
                round=False
            )
            qty_todo = float_round(
                new_qty - sum(move_workorder_lines.mapped('qty_to_consume')),
                precision_rounding=rounding)

            # Remove or lower quantity on exisiting workorder lines
            if float_compare(qty_todo, 0.0, precision_rounding=rounding) < 0:
                qty_todo = abs(qty_todo)
                # Try to decrease or remove lines that are not reserved and
                # partialy reserved first. A different decrease strategy could
                # be define in _unreserve_order method.
                for wo_line in move_workorder_lines.sorted(
                        key=lambda wl: wl._unreserve_order()):
                    if float_compare(qty_todo, 0,
                                     precision_rounding=rounding) <= 0:
                        break
                    # If the quantity to consume on the line is lower than the
                    # quantity to remove, the line could be remove.
                    if float_compare(
                            wo_line.qty_to_consume,
                            qty_todo, precision_rounding=rounding) <= 0:
                        qty_todo = float_round(
                            qty_todo - wo_line.qty_to_consume,
                            precision_rounding=rounding)
                        if line_values['to_delete']:
                            line_values['to_delete'] |= wo_line
                        else:
                            line_values['to_delete'] = wo_line
                    # decrease the quantity on the line
                    else:
                        new_val = wo_line.qty_to_consume - qty_todo
                        # avoid to write a negative reserved quantity
                        new_reserved = max(
                            0, wo_line.qty_reserved - qty_todo)
                        line_values['to_update'][wo_line] = {
                            'qty_to_consume': new_val,
                            'qty_done': new_val,
                            'qty_reserved': new_reserved,
                        }
                        qty_todo = 0
            else:
                # Search among wo lines which one could be updated
                qty_reserved_wl = defaultdict(float)
                # Try to update the line with the greater reservation first in
                # order to promote bigger batch.
                for wo_line in move_workorder_lines.sorted(
                        key=lambda wl: wl.qty_reserved, reverse=True):
                    rounding = wo_line.product_uom_id.rounding
                    if float_compare(
                            qty_todo, 0, precision_rounding=rounding) <= 0:
                        break
                    move_lines = wo_line._get_move_lines()
                    qty_reserved_wl[wo_line.lot_id] += wo_line.qty_reserved
                    # The reserved quantity according to exisiting move line
                    # already produced (with qty_done set) and other production
                    # lines with the same lot that are currently on production.
                    qty_reserved_remaining = sum(
                        move_lines.mapped('product_uom_qty')
                    ) - sum(
                        move_lines.mapped('qty_done')
                    ) - qty_reserved_wl[wo_line.lot_id]
                    consumed_qty = wo_line.qty_to_consume
                    if float_compare(qty_reserved_remaining, 0,
                                     precision_rounding=rounding) > 0:
                        qty_to_add = min(qty_reserved_remaining, qty_todo)
                        line_values['to_update'][wo_line] = {
                            'qty_done': consumed_qty + qty_to_add,
                            'qty_to_consume': consumed_qty + qty_to_add,
                            'qty_reserved': wo_line.qty_reserved + qty_to_add,
                        }
                        qty_todo -= qty_to_add
                        qty_reserved_wl[wo_line.lot_id] += qty_to_add

                    # If a line exists without reservation and without lot. It
                    # means that previous operations could not find any
                    # reserved quantity and created a line without lot
                    # prefilled. In this case, the system will not find an
                    # existing move line with available reservation anymore
                    # and will increase this line instead of creating a new
                    # line without lot and reserved quantities.
                    if not wo_line.qty_reserved and not \
                            wo_line.lot_id and (
                            wo_line.product_tracking != 'serial' or
                            wo_line.partial_serialization_type != 'serial'):
                        line_values['to_update'][wo_line] = {
                            'qty_done': consumed_qty + qty_todo,
                            'qty_to_consume': consumed_qty + qty_todo,
                        }
                        qty_todo = 0

                # if there are still qty_todo, create new wo lines
                if float_compare(
                        qty_todo, 0.0, precision_rounding=rounding) > 0:
                    for values in self._generate_lines_values(move, qty_todo):
                        line_values['to_create'].append(values)
        if line_values['to_update']:
            steps = self._get_quality_points([{
                'product_id': record.product_id.id
            } for record in line_values['to_update'].keys()])
            # steps = self._get_quality_points([{'product_id': record.
            # product_id.id} for record in res['to_update'].keys()])
            for line, values in line_values['to_update'].items():
                if line.product_id in steps.mapped('component_id') or \
                        line.move_id.product_id.is_serialization_product():
                    values['qty_done'] = 0
        return line_values

    @api.model
    def _generate_lines_values(self, move, qty_to_consume):
        """ Create workorder line. First generate line based on the reservation,
        in order to prefill reserved quantity, lot and serial number.
        If the quantity to consume is greater than the reservation quantity
        then create line with the correct quantity to consume but without
        lot or serial number.
        """
        lines = []
        is_tracked = move.product_id.tracking != 'none' or \
                     move.product_id.is_serial_product()
        if move in self.move_raw_ids._origin:
            # Get the inverse_name (many2one on line) of raw_workorder_line_ids
            initial_line_values = {
                self.raw_workorder_line_ids.
                    _get_raw_workorder_inverse_name(): self.id}
        else:
            # Get the inverse_name (many2one on line) of
            # finished_workorder_line_ids
            initial_line_values = {
                self.finished_workorder_line_ids.
                    _get_finished_workoder_inverse_name(): self.id
            }
        for move_line in move.move_line_ids:
            line = dict(initial_line_values)
            if float_compare(
                    qty_to_consume,
                    0.0,
                    precision_rounding=move.product_uom.rounding) <= 0:
                break
            # move line already 'used' in workorder (from its lot for instance)
            if move_line.lot_produced_ids or float_compare(
                    move_line.product_uom_qty,
                    move_line.qty_done,
                    precision_rounding=move.product_uom.rounding
            ) <= 0:
                continue
            # search wo line on which the lot is not
            # fully consumed or other reserved lot
            linked_wo_line = self._workorder_line_ids().filtered(
                lambda line: line.move_id == move and
                             line.lot_id == move_line.lot_id
            )
            if linked_wo_line:
                if float_compare(
                        sum(linked_wo_line.mapped('qty_to_consume')),
                        move_line.product_uom_qty - move_line.qty_done,
                        precision_rounding=move.product_uom.rounding) < 0:
                    to_consume_in_line = min(
                        qty_to_consume,
                        move_line.product_uom_qty - move_line.qty_done - sum(
                            linked_wo_line.mapped('qty_to_consume')))
                else:
                    continue
            else:
                to_consume_in_line = min(
                    qty_to_consume,
                    move_line.product_uom_qty - move_line.qty_done)
            line.update({
                'move_id': move.id,
                'product_id': move.product_id.id,
                'product_uom_id': is_tracked and
                                  move.product_id.uom_id.id or
                                  move.product_uom.id,
                'qty_to_consume': to_consume_in_line,
                'qty_reserved': to_consume_in_line,
                'lot_id': move_line.lot_id.id,
                'qty_done': to_consume_in_line,
            })
            lines.append(line)
            qty_to_consume -= to_consume_in_line
        # The move has not reserved the whole
        # quantity so we create new wo lines
        if float_compare(qty_to_consume, 0.0,
                         precision_rounding=move.product_uom.rounding) > 0:
            line = dict(initial_line_values)
            if move.product_id.is_serial_product():
                while float_compare(
                        qty_to_consume, 0.0,
                        precision_rounding=move.product_uom.rounding) > 0:
                    line.update({
                        'move_id': move.id,
                        'product_id': move.product_id.id,
                        'product_uom_id': move.product_id.uom_id.id,
                        'qty_to_consume': 1,
                        'qty_done': 1,
                    })
                    lines.append(line)
                    qty_to_consume -= 1
            else:
                line.update({
                    'move_id': move.id,
                    'product_id': move.product_id.id,
                    'product_uom_id': move.product_uom.id,
                    'qty_to_consume': qty_to_consume,
                    'qty_done': qty_to_consume,
                })
                lines.append(line)
        steps = self._get_quality_points(lines)
        for line in lines:
            if line['product_id'] in steps.mapped('component_id.id') or \
                    move.product_id.is_serialization_product():
                line['qty_done'] = 0
        return lines

    def _update_finished_move(self):
        """

        Update the finished move & move lines in order to set the finished
        product lot on it as well as the produced quantity.
        This method get the information either from the last workorder
        or from the Produce wizard.

        :return: None or Raise Error
        :raise: User Error
        """
        production_move = self.production_id.move_finished_ids.filtered(
            lambda move: move.product_id == self.product_id and
                         move.state not in ('done', 'cancel')
        )
        if production_move and (
                production_move.product_id.is_serialization_product()):
            if not self.finished_lot_id:
                raise UserError(_(
                    'You need to provide a lot for the finished product.'
                ))
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
                dest_id = production_move.location_dest_id \
                              ._get_putaway_strategy(self.product_id) \
                              .id or production_move.location_dest_id.id
                move_line.create({
                    'move_id': production_move.id,
                    'product_id': production_move.product_id.id,
                    'lot_id': self.finished_lot_id.id,
                    'product_uom_qty': self.qty_producing,
                    'product_uom_id': self.product_uom_id.id,
                    'qty_done': self.qty_producing,
                    'location_id': production_move.location_id.id,
                    'location_dest_id': dest_id,
                })
        else:
            rounding = production_move.product_uom.rounding
            production_move._set_quantity_done(
                float_round(self.qty_producing, precision_rounding=rounding)
            )

    def action_print(self):
        """

        :return: Report Action or Error
        :raise: User Error
        """
        if self.product_id.uom_id.category_id.measure_type == 'unit':
            qty = int(self.qty_producing)
        else:
            qty = 1
        quality_point_id = self.current_quality_check_id.point_id
        report_type = quality_point_id.test_report_type
        if not self.product_id.is_serialization_product():
            if report_type == 'zpl':
                xml_id = 'stock.label_barcode_product_product'
            else:
                xml_id = 'product.report_product_product_barcode'
            res = self.env.ref(xml_id).report_action(
                [self.product_id.id] * qty)
        else:
            if self.finished_lot_id:
                if report_type == 'zpl':
                    xml_id = 'stock.label_lot_template'
                else:
                    xml_id = 'stock.action_report_lot_label'
                res = self.env.ref(xml_id).report_action(
                    [self.finished_lot_id.id] * qty)
            else:
                raise UserError(_(
                    'You did not set a lot/serial '
                    'number for the final product'))
        res['id'] = self.env.ref(xml_id).id
        # The button goes immediately to the next step
        self._next()
        return res

    def _next(self, continue_production=False):
        """

        :param continue_production:
        :return: Super return or Raise Error
        :raise: User Error
        """
        self.ensure_one()
        if self.test_type in ('register_byproducts',
                              'register_consumed_materials'):
            if self.component_partial_tracking != 'none' and not self.lot_id \
                    and self.qty_done != 0:
                raise UserError(_('Please enter a Lot/SN.'))
        return super(MrpProductionWorkcenterLine, self)._next(
            continue_production=continue_production)

    # tracking
    def _create_checks(self):
        qc_checks = self.env['quality.check']
        for wo in self:
            # Track components which have a control point
            processed_move = self.env['stock.move']
            production = wo.production_id
            points = self.env['quality.point'].search([
                ('operation_id', '=', wo.operation_id.id),
                ('picking_type_id', '=', production.picking_type_id.id),
                ('company_id', '=', wo.company_id.id),
                '|', ('product_id', '=', production.product_id.id),
                '&', ('product_id', '=', False),
                ('product_tmpl_id', '=',
                 production.product_id.product_tmpl_id.id)])
            move_raw_ids_in_context = self._context.get('move_raw_ids', False)
            move_finished_ids_context = self._context.get('move_finished_ids', False)
            if move_raw_ids_in_context:
                move_raw_ids = move_raw_ids_in_context
                move_finished_ids = move_finished_ids_context
            else:
                move_raw_ids = wo.move_raw_ids.filtered(
                    lambda m: m.state not in ('done', 'cancel'))
                move_finished_ids = wo.move_finished_ids.filtered(
                    lambda m: m.state not in ('done', 'cancel'))
            values_to_create = []
            check_count = max(wo.check_ids.mapped('sequence')) + 1 if wo.check_ids else 1
            for point in points:
                # Check if we need a quality control for this point
                if point.check_execute_now():
                    moves = self.env['stock.move']
                    values = {
                        'workorder_id': wo.id,
                        'point_id': point.id,
                        'team_id': point.team_id.id,
                        'company_id': wo.company_id.id,
                        'product_id': production.product_id.id,
                        # Two steps are from the same production
                        # if and only if the produced quantities
                        # at the time they were created are equal.
                        'finished_product_sequence': wo.qty_produced,
                    }
                    if point.test_type == 'register_byproducts':
                        moves = move_finished_ids.filtered(
                            lambda m: m.product_id == point.component_id)
                    elif point.test_type == 'register_consumed_materials':
                        moves = move_raw_ids.filtered(
                            lambda m: m.product_id == point.component_id)
                    else:
                        values.update({'sequence': check_count})
                        check_count += 1
                        values_to_create.append(values)
                    # Create 'register ...' checks
                    for move in moves:
                        check_vals = values.copy()
                        check_vals.update({'sequence': check_count})
                        check_vals.update(wo._defaults_from_workorder_lines(
                            move, point.test_type))
                        values_to_create.append(check_vals)
                        check_count += 1
                    processed_move |= moves

            # Generate quality checks associated with unreferenced components
            moves_without_check = (
                    (move_raw_ids | move_finished_ids) - processed_move
            ).filtered(lambda move: move.has_tracking != 'none' or
                                    move.product_id.partial_serialization_id)
            quality_team_id = self.env['quality.alert.team'].search(
                [], limit=1).id
            for move in moves_without_check:
                values = {
                    'workorder_id': wo.id,
                    'product_id': production.product_id.id,
                    'company_id': wo.company_id.id,
                    'component_id': move.product_id.id,
                    'team_id': quality_team_id,
                    # Two steps are from the same production
                    # if and only if the produced quantities
                    # at the time they were created are equal.
                    'finished_product_sequence': wo.qty_produced,
                }
                if move in move_raw_ids:
                    test_type = self.env.ref(
                        'mrp_workorder.test_type_register_consumed_materials')
                if move in move_finished_ids:
                    test_type = self.env.ref(
                        'mrp_workorder.test_type_register_byproducts')
                values.update({'test_type_id': test_type.id, 'sequence': check_count})
                values.update(wo._defaults_from_workorder_lines(
                    move, test_type.technical_name))
                values_to_create.append(values)
            qc_checks.create(values_to_create)
            # Set default quality_check
            wo.skip_completed_checks = False
            wo._change_quality_check(position=0)

    def _get_byproduct_move_to_update(self):
        moves = super(
            MrpProductionWorkcenterLine, self)._get_byproduct_move_to_update()
        return moves.filtered(
            lambda m: not m.product_id.tracking.is_serialization_product())

    def record_production(self):
        """

        :return: Boolean or Raise Error
        :raise: User Error
        """
        if any([(x.quality_state == 'none') for x in self.check_ids]):
            raise UserError(_('You still need to do the quality checks!'))
        is_serial = self.production_id.product_id.is_serialization_product()
        if is_serial and not self.finished_lot_id and self.move_raw_ids:
            raise UserError(_(
                'You should provide a lot for the final product'))
        if self.check_ids:
            # Check if you can attribute the lot to the checks
            if is_serial and self.finished_lot_id:
                self.check_ids.filtered(
                    lambda check: not check.finished_lot_id
                ).write({
                    'finished_lot_id': self.finished_lot_id.id
                })
        if not self:
            return True
        self.ensure_one()
        self._check_company()
        if float_compare(
                self.qty_producing, 0,
                precision_rounding=self.product_uom_id.rounding) <= 0:
            raise UserError(_(
                'Please set the quantity you are currently producing.'
                'It should be different from zero.'))

        # If last work order, then post lots used
        if not self.next_work_order_id and not self._context.get('no_need_to_update_moves', False):
            self._update_finished_move()

        # Transfer quantities from temporary
        # to final move line or make them final
        self._update_moves()

        # Transfer lot (if present) and quantity
        # produced to a finished workorder line
        if self.product_id.is_serialization_product:
            self._create_or_update_finished_line()
        # Update workorder quantity produced
        self.qty_produced += self.qty_producing

        # Suggest a finished lot on the next workorder
        if self.next_work_order_id and (
                self.production_id.product_id.tracking != 'none' or
                self.production_id.product_id.partial_serialization_id
        ) and not self.next_work_order_id.finished_lot_id:
            self.next_work_order_id._defaults_from_finished_workorder_line(
                self.finished_workorder_line_ids)
            # As we may have changed the quantity
            # to produce on the next workorder,
            # make sure to update its wokorder lines
            self.next_work_order_id._apply_update_workorder_lines()

        # One a piece is produced, you can launch the next work order
        self._start_nextworkorder()

        # Test if the production is done
        rounding = self.production_id.product_uom_id.rounding
        if float_compare(
                self.qty_produced, self.production_id.product_qty,
                precision_rounding=rounding) < 0:
            previous_wo = self.env['mrp.workorder']
            if self.product_id.is_serialization_product():
                previous_wo = previous_wo.search([
                    ('next_work_order_id', '=', self.id)
                ])
            candidate_found_in_previous_wo = False
            if previous_wo:
                candidate_found_in_previous_wo = self. \
                    _defaults_from_finished_workorder_line(
                    previous_wo.finished_workorder_line_ids)
            if not candidate_found_in_previous_wo:
                # self is the first workorder
                self.qty_producing = self.qty_remaining
                self.finished_lot_id = False
                if self.product_id.is_serial_product():
                    self.qty_producing = 1

            self._apply_update_workorder_lines()
        else:
            self.qty_producing = 0
            self.button_finish()

        rounding = self.product_uom_id.rounding
        if self.production_id.picking_type_id.backflush_on_mo_completion:
            self.production_id.with_context(no_need_to_finished_lines=True).post_inventory()
        if float_compare(self.qty_producing, 0,
                         precision_rounding=rounding) > 0:
            self._create_checks()
        return True

    def on_barcode_scanned(self, barcode):
        # qty_done field for serial numbers is fixed
        if self.component_tracking != 'serial' or \
                self.component_partial_tracking != 'serial':
            if not self.lot_id:
                # not scanned yet
                self.qty_done = 1
            elif self.lot_id.name == barcode:
                self.qty_done += 1
            else:
                return {
                    'warning': {
                        'title': _("Warning"),
                        'message': _(
                            "You are using components from another lot. "
                            "\nPlease validate the components from "
                            "the first lot before using another lot.")
                    }
                }
        lot = self.env['stock.production.lot'].search([
            ('name', '=', barcode)])
        if self.component_tracking or self.component_partial_tracking:
            if not lot:
                # create a new lot
                # create in an onchange is necessary here
                # ("new" cannot work here)
                lot = self.env['stock.production.lot'].create({
                    'name': barcode,
                    'product_id': self.component_id.id,
                    'company_id': self.company_id.id,
                })
            self.lot_id = lot
        elif self.production_id.product_id.is_serialization_product():
            if not lot:
                lot = self.env['stock.production.lot'].create({
                    'name': barcode,
                    'product_id': self.product_id.id,
                    'company_id': self.company_id.id,
                })
            self.finished_lot_id = lot

    @api.onchange('finished_lot_id')
    def _onchange_finished_lot_id(self):
        """

        When the user changes the lot being currently produced, suggest
        a quantity to produce consistent with the previous workorders.

        :return: None or Raise Error
        :raise: User Error
        """
        finished_id = list(set(
            self.production_id.workorder_ids.filtered(
                lambda w: w.state == 'done'
            ).mapped('finished_lot_id')))
        # if finished_id and self.finished_lot_id and \
        #         self.finished_lot_id not in finished_id:
        #     raise UserError(_(
        #         "Please select same Lot/Serial number "
        #         "that you have used in finished WO."))
        previous_wo = self.env['mrp.workorder'].search([
            ('next_work_order_id', '=', self.id)
        ])
        if previous_wo:
            line = previous_wo.finished_workorder_line_ids.filtered(
                lambda l: l.product_id == self.product_id and
                          l.lot_id == self.finished_lot_id)
            if line:
                self.qty_producing = line.qty_done

    def check_splits_allowed(self):
        self.production_id.check_splits_allowed()

    def action_generate_serial_for_component(self):
        self.ensure_one()
        self.lot_id = self.env['stock.production.lot'].create({
            'product_id': self.component_id.id,
            'company_id': self.company_id.id,
        })

    def write(self, values):
        if 'production_id' in values:
            raise UserError(_('You cannot link this work order to another manufacturing order.'))
        if 'workcenter_id' in values:
            for workorder in self:
                if workorder.workcenter_id.id != values['workcenter_id']:
                    if workorder.state in ('progress', 'done', 'cancel'):
                        raise UserError(
                            _('You cannot change the workcenter of a work order that is in progress or done.'))
                    workorder.leave_id.resource_id = self.env['mrp.workcenter'].browse(
                        values['workcenter_id']).resource_id
        # if list(values.keys()) != ['time_ids'] and any(workorder.state == 'done' for workorder in self) and not self._context.get("force", False):
        #     raise UserError(_('You can not change the finished work order.'))
        if 'date_planned_start' in values or 'date_planned_finished' in values:
            for workorder in self:
                start_date = fields.Datetime.to_datetime(
                    values.get('date_planned_start')) or workorder.date_planned_start
                end_date = fields.Datetime.to_datetime(
                    values.get('date_planned_finished')) or workorder.date_planned_finished
                if start_date and end_date and start_date > end_date:
                    raise UserError(
                        _('The planned end date of the work order cannot be prior to the planned start date, please correct this to save the work order.'))
                # Update MO dates if the start date of the first WO or the
                # finished date of the last WO is update.
                if workorder == workorder.production_id.workorder_ids[0] and 'date_planned_start' in values:
                    workorder.production_id.with_context(force_date=True).write({
                        'date_planned_start': fields.Datetime.to_datetime(values['date_planned_start'])
                    })
                if workorder == workorder.production_id.workorder_ids[-1] and 'date_planned_finished' in values:
                    workorder.production_id.with_context(force_date=True).write({
                        'date_planned_finished': fields.Datetime.to_datetime(values['date_planned_finished'])
                    })
        if 'sequence' in values and self.state in ["done", "cancel"]:
            raise UserError("You can not reorder cancelled or finished workorder.")

        res = super(models.Model, self).write(values)
        # Manage Check IDS sequence
        checking_not_done_qcps = self.check_ids.filtered(lambda c: c.quality_state == 'none')
        if 'check_ids' in values and checking_not_done_qcps:
            self.write({'current_quality_check_id': checking_not_done_qcps[0].id})
        # Manage workorder sequence
        if 'sequence' in values and not self._context.get('no_need_to_update', False):
            self.align_workorders()
        return res

    # Splitting MO for bad quality lots
    def button_mo_split(self, finished_lots):
        self.production_id.button_mo_split(finished_lots=finished_lots)
        return True

    def align_workorders(self):
        for production_id in self.mapped('production_id'):
            workorder_ids = production_id.workorder_ids.sorted(
                key=lambda record: record.sequence).filtered(lambda wo: wo.state not in ['done', 'cancel'])
            last_index = len(workorder_ids) - 1
            update_vals = {'next_work_order_id': workorder_ids[1].id, 'previous_workorder_id': False}
            for index, workorder in enumerate(workorder_ids):
                update_vals['state'] = 'ready' if index == 0 and workorder.state == 'pending'\
                    else 'pending' if index != 0 and workorder.state == 'ready' else workorder.state
                update_vals['previous_workorder_id'] = workorder.id
                update_vals['next_work_order_id'] = False if index == last_index else workorder_ids[index+1]
                workorder.with_context(no_need_to_update=True).update(update_vals)
        return True

    def _change_quality_check(self, **params):
        self.ensure_one()
        check_id = None
        # Determine the list of checks to consider
        checks = params['checks'] if 'checks' in params else self.check_ids
        if not params.get('children'):
            checks = checks.filtered(lambda c: not c.parent_id)
        # We need to make sure the current quality check is in our list
        # when we compute position relatively to the current quality check.
        if 'increment' in params or 'checks' in params and self.current_quality_check_id not in checks:
            checks |= self.current_quality_check_id
        # Restrict to checks associated with the current production
        checks = checks.filtered(lambda c: c.finished_product_sequence == self.qty_produced)
        # As some checks are generated on the fly,
        # we need to ensure that all 'children' steps are grouped together.
        # Missing steps are added at the end.
        # ------------- Removed sorting logic as we required to sort this in order with sequence -----
        ordered_check_ids = checks.sorted(key=lambda r: r.sequence).ids
        # We manually add a final 'Summary' step
        # which is not associated with a specific quality_check (hence the 'False' id).
        ordered_check_ids.append(False)
        # Determine the quality check we are switching to
        if 'increment' in params:
            current_id = self.current_quality_check_id.id
            position = ordered_check_ids.index(current_id)
            check_id = self.current_quality_check_id.id
            if position + params['increment'] in range(0, len(ordered_check_ids)):
                position += params['increment']
                check_id = ordered_check_ids[position]
        elif params.get('position') in range(0, len(ordered_check_ids)):
            position = params['position']
            check_id = ordered_check_ids[position]
        elif params.get('goto') in ordered_check_ids:
            check_id = params['goto']
            position = ordered_check_ids.index(check_id)
        # Change the quality check and the worksheet page if necessary
        if check_id is not None:
            next_check = self.env['quality.check'].browse(check_id)
            change_worksheet_page = position != len(ordered_check_ids) - 1 and next_check.point_id.worksheet == 'scroll'
            self.write({
                'allow_producing_quantity_change': True if params.get('position') == 0 and all(c.quality_state == 'none' for c in self.check_ids) else False,
                'current_quality_check_id': check_id,
                'is_first_step': position == 0,
                'is_last_step': check_id == False,
                'worksheet_page': next_check.point_id.worksheet_page if change_worksheet_page else self.worksheet_page,
            })


class MrpWorkorderLine(models.Model):
    _inherit = 'mrp.workorder.line'

    partial_serialization_id = fields.Many2one(
        related="product_id.partial_serialization_id", store=True)
    partial_serialization_type = fields.Selection(
        related="product_id.partial_serialization_id.traceability_type",
        string="Product tracking", readonly=True, store=True)
