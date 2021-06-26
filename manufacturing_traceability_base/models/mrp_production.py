# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models, fields, _, api
from odoo.exceptions import UserError


class MrpProduction(models.Model):
	"""Manufacturing Orders

	"""
	_inherit = 'mrp.production'

	finished_product_tracking = fields.Selection(related="product_id.tracking", store=True)
	backflush_on_mo_completion = fields.Boolean(
		string="Backflush on WO Completion",
		related="picking_type_id.backflush_on_mo_completion", store=True)
	splits_allowed = fields.Boolean(string="Splits Allowed",
									related="picking_type_id.splits_allowed", store=True)
	operation_edit_allowed = fields.Boolean(string="Operation Edits Allowed",
											related="picking_type_id.operation_edit_allowed",
											store=True)
	split_order_source_id = fields.Many2one('mrp.production', string="Split Order Source")
	able_to_see_split = fields.Boolean(compute="compute_able_to_see_split")
	splitted_mo_count = fields.Integer(compute="compute_splitted_mo")

	def compute_splitted_mo(self):
		for rec in self:
			rec.splitted_mo_count = self.search_count([('split_order_source_id', '=', rec.id)])

	def action_view_splitted_mos(self):
		return {
			'name': 'Splitted Manufacturing Orders',
			'view_mode': 'tree,form',
			'res_model': self._name,
			'domain': [('picking_type_id.active', '=', True), ('split_order_source_id', '=', self.id)],
			'type': 'ir.actions.act_window',
			'context': {'no_create_edit': True, 'search_default_todo': True}
		}

	def action_view_source_mo(self):
		return {
			'name': 'Splitted Manufacturing Orders',
			'view_mode': 'form',
			'res_model': self._name,
			'domain': [('picking_type_id.active', '=', True), ('id', '=', self.split_order_source_id.id)],
			'res_id': self.split_order_source_id.id,
			'type': 'ir.actions.act_window',
			'context': {'no_create_edit': True, 'search_default_todo': True}
		}

	def compute_able_to_see_split(self):
		for rec in self:
			rec.able_to_see_split = True if rec.workorder_ids.filtered(
				lambda w: w.qty_produced > 0) and rec.splits_allowed \
				and rec.finished_product_tracking == 'serial' else False

	# Overridden to change the source location logic

	def _get_move_raw_values(self, bom_line, line_data):
		data = super(MrpProduction, self)._get_move_raw_values(
			bom_line, line_data)
		old_location = data['location_id']
		new_location = bom_line.operation_id.location_id.id if bom_line.operation_id.location_id else old_location
		data['location_id'] = new_location
		return data

	@api.onchange('location_src_id', 'move_raw_ids', 'routing_id')
	def _onchange_location(self):
		# Remove all code so that we can manually set source location
		pass

	# what-if? Redefine show_final_lots
	# show_final_lots = fields.Boolean(string='Show Final Lots',
	#                                  compute='_compute_show_lots')
	# what-if? Redefine post_visible
	# post_visible = fields.Boolean(
	#     string='Allowed to Post Inventory', compute='_compute_post_visible',
	#     help='Technical field to check when we can post')

	def create_workorder_for_given_operation(self, operation_id, with_route=False):
		# Initial qty producing
		starting_sequence = len(self.workorder_ids) + 1
		quantity = max(self.product_qty - sum(
			self.move_finished_ids.filtered(lambda move: move.product_id == self.product_id).mapped('quantity_done')), 0)
		quantity = self.product_id.uom_id._compute_quantity(quantity, self.product_uom_id)
		if self.product_id.tracking == 'serial':
			quantity = 1.0
		workorders = self.env['mrp.workorder']
		routes = False
		if with_route:
			routes = self.env['mrp.routing'].browse(operation_id)
		operation_ids = [operation_id] if not with_route else list(set(routes.mapped('operation_ids')))
		if operation_ids:
			for operation in operation_ids:
				workorder = workorders.create({
					'name': operation.name,
					'production_id': self.id,
					'workcenter_id': operation.workcenter_id.id,
					'product_uom_id': self.product_id.uom_id.id,
					'operation_id': operation.id,
					'state': 'pending',
					'sequence': starting_sequence,
					'qty_producing': quantity,
					'consumption': self.bom_id.consumption,
				})
				starting_sequence += 1
				workorders += workorder
				moves_raw = self.move_raw_ids.filtered(
					lambda move: move.operation_id.id == operation.id and
								 move.bom_line_id.bom_id.routing_id.id == self.bom_id.routing_id.id)
				moves_finished = self.move_finished_ids.filtered(lambda move: move.operation_id == operation)
				# Commented below code for future purpose
				# if len(workorders) == len(operation):
				# 	moves_raw |= self.move_raw_ids.filtered(lambda move: not move.operation_id and
				# 														 move.bom_line_id.bom_id.routing_id ==
				# 														 self.bom_id.routing_id)
				# 	moves_raw |= self.move_raw_ids.filtered(lambda move: not move.workorder_id and not move.bom_line_id.bom_id.routing_id)
				#
				# 	moves_finished |= self.move_finished_ids.filtered(lambda move: move.product_id != self.product_id and not move.operation_id)
				moves_raw.mapped('move_line_ids').write({'workorder_id': workorder.id})
				(moves_finished | moves_raw).write({'workorder_id': workorder.id})
				# When we add products here than we will uncomment below line
				# workorder._create_checks()
				workorder._generate_wo_lines()

		# Get back to workorder list
		workorder_list_action = self.env.ref('mrp.action_mrp_workorder_production_specific').read()[0]
		workorder_list_action.update({
			'domain': [('production_id', '=', self.id)]
		})
		workorders.align_workorders()
		return workorders, workorder_list_action

	def action_mrp_workorder_production_specific(self):
		workorder_list_action = self.env.ref('mrp.action_mrp_workorder_production_specific').read()[0]
		workorder_list_action['context'] = {
			'operation_edit_allowed': self.operation_edit_allowed,
			'need_to_create_wo': True,
			'is_manufacturing_admin': self.user_has_groups('mrp.group_mrp_manager'),
		}
		workorder_list_action['domain'] = [('production_id', '=', self.id)]
		return workorder_list_action

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

	def button_update_wo(self, move, operation_id):
		""" Update WO based on Operation selected on Components Lines"""
		if not operation_id or not move:
			return True
		routing_operation = self.env['mrp.routing.workcenter']
		new_operation = routing_operation.browse(operation_id)
		old_operation = move.operation_id
		if new_operation and old_operation:
			new_wo = self.workorder_ids.filtered(lambda x : x.operation_id == new_operation)
			old_wo = self.workorder_ids.filtered(lambda x : x.operation_id == old_operation)

			old_move_raw_ids = self.move_raw_ids.filtered(lambda x: x.workorder_id == old_wo and x.product_id == move.product_id)
			old_move_raw_ids.write({'workorder_id': new_wo.id})
			old_move_raw_ids.mapped('move_line_ids').write({'workorder_id': new_wo.id})

			raw_workorder_ids = old_wo.raw_workorder_line_ids.filtered(lambda x : x.product_id == move.product_id)
			raw_workorder_ids.write({'raw_workorder_id': new_wo.id})

			need_check_ids = old_wo.check_ids.filtered(lambda x : x.point_id)
			component_check_ids = old_wo.check_ids.filtered(lambda x: x.component_id == move.product_id)
			copy_to_new_wo_checks = component_check_ids - need_check_ids
			copy_to_new_wo_checks.write({'workorder_id': new_wo.id})


			def check_last_step(workorder_ids):
				"""Manage Last Step on WOrkorder if that doesn't have any
				components. Based on component list is_last_step will be managed."""
				for wo in workorder_ids:
					if not wo.check_ids:
						wo.is_last_step = True
					else:
						wo.is_last_step = False
			# Manage last
			check_last_step(workorder_ids=[old_wo, new_wo])

			old_wo.current_quality_check_id = old_wo.check_ids and old_wo.check_ids.filtered(lambda x: x.quality_state == 'none')[0] or False
			new_wo.current_quality_check_id = new_wo.check_ids and new_wo.check_ids.filtered(lambda x: x.quality_state == 'none')[0] or False

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
		for index, operation in enumerate(bom.routing_id.operation_ids):
			workorder = workorders.create({
				'name': operation.name,
				'production_id': self.id,
				'workcenter_id': operation.workcenter_id.id,
				'product_uom_id': self.product_id.uom_id.id,
				'operation_id': operation.id,
				'state': len(workorders) == 0 and 'ready' or 'pending',
				'qty_producing': quantity,
				'consumption': self.bom_id.consumption,
				'sequence': index + 1,
			})
			if workorders:
				workorders[-1].next_work_order_id = workorder.id
				workorders[-1]._start_nextworkorder()
			workorders += workorder

			moves_raw = self.move_raw_ids.filtered(
				lambda move: move.operation_id == operation)
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

	def check_splits_allowed(self):
		if not self.splits_allowed:
			raise UserError("Splits is not allowed for this type of manufacturing!!")
		# Check done workorder for selected Finished LOT.
		# if finished_lot_ids and len(set(self.move_raw_ids.filtered(lambda x: x.state == 'done' and all(lot_id for lot_id in x.move_line_ids.mapped('lot_produced_ids') if lot_id in finished_lot_ids)).mapped('quantity_done'))) != 1:
		#     raise UserError("The selected serial numbers have not completed the same statement\
		#         of work on this Manufacturing order. They cannot be split together.\
		#         You must either record production for each of them through the same work order or split them out into separate unique Manufacturing Orders")

	def manage_checks(self, old_workorder, new_workorder, finished_lots):
		old_workorder.check_ids.filtered(lambda w: w.finished_lot_id.id in finished_lots.ids).write({
			'workorder_id': new_workorder.id,
		})
		for check in old_workorder.check_ids.filtered(lambda w: w.finished_lot_id.id not in finished_lots.ids):
			finished_product_sequence = check.finished_product_sequence - len(finished_lots)
			if finished_product_sequence < 0:
				finished_product_sequence = 0
			check.write({
				'finished_product_sequence': finished_product_sequence
			})
		if new_workorder.state != 'done':
			for remaining_checks in old_workorder.check_ids:
				remaining_checks.copy({
					'workorder_id': new_workorder.id,
					'qty_done': 0,
					'quality_state': 'none',
				})
			new_workorder.current_quality_check_id = new_workorder.check_ids[-1].id if new_workorder.check_ids else False
			new_workorder.workorder_line_id = new_workorder.raw_workorder_line_ids[0].id if \
				new_workorder.raw_workorder_line_ids else False
			new_workorder.raw_workorder_line_ids.check_ids = [(6, 0, new_workorder.current_quality_check_id.ids)]

	def create_produce_lines(self, workorder, finished_lots):
		for lot in finished_lots:
			self.env['mrp.workorder.line'].create({
				'finished_workorder_id': workorder.id,
				'product_id': lot.product_id.id,
				'lot_id': lot.id,
				'qty_done': 1,
			})

	def update_backflushing_moves(self, splitted_mo, finished_lots):
		# Move raw ids to new mo
		self.move_raw_ids.filtered(
			lambda m: any(lot for lot in m.mapped('move_line_ids.lot_id').ids if lot in finished_lots.ids)
					  and m.state == 'done').write({'raw_material_production_id': splitted_mo.id,
													'reference': splitted_mo.name})
		# Update finished move to new mo
		self.move_finished_ids.filtered(
			lambda m: any(lot for lot in m.mapped('move_line_ids.lot_id').ids if lot in finished_lots.ids)
					  and m.state == 'done').write({'production_id': splitted_mo.id, 'reference': splitted_mo.name})

	def create_workorder_for_new_mo(self, splitted_mo, finished_lots, backflushing):
		for workorder in self.workorder_ids:
			workorder.copy({
				'production_id': splitted_mo.id,
				'qty_produced': 0,
			})
		for workorder in zip(self.workorder_ids, splitted_mo.workorder_ids):
			old_workorder = workorder[0]
			new_workorder = workorder[1]
			self.manage_checks(old_workorder=old_workorder, new_workorder=new_workorder, finished_lots=finished_lots)
			old_workorder.qty_produced -= len(finished_lots)
			# Deleting finished lines from wo
			old_workorder.finished_workorder_line_ids.filtered(lambda f: f.lot_id.id in finished_lots.ids).unlink()
			old_workorder._refresh_wo_lines()
			new_workorder._refresh_wo_lines()
			for lot in finished_lots:
				new_workorder.qty_producing = 1
				if not new_workorder.next_work_order_id:
					new_workorder.finished_lot_id = lot.id
					new_workorder.product_uom_id = old_workorder.product_uom_id.id
					new_workorder.with_context(no_need_to_update_moves=backflushing).do_finish()
				else:
					new_workorder.with_context(no_need_to_update_moves=backflushing).record_production()
			if backflushing:
				old_workorder.move_raw_ids.filtered(lambda m: m.state == 'done').write({
					'raw_material_production_id': splitted_mo.id,
					'workorder_id': new_workorder.id,
				})
				self.create_produce_lines(workorder=new_workorder, finished_lots=finished_lots)

	def get_move_raws(self, finished_lots):
		move_raws_with_finished_lot = self.env['stock.move']
		for lot_id in finished_lots:
			move_raws_with_finished_lot += self.move_raw_ids.filtered(lambda x: lot_id in x.move_line_ids.mapped('lot_produced_ids'))
		remaining_product_ids = self.bom_id.bom_line_ids.mapped('product_id') - move_raws_with_finished_lot.mapped('product_id')
		remaining_move_raws_without_finished_lot = self.move_raw_ids.filtered(lambda x: x.product_id in remaining_product_ids)
		return move_raws_with_finished_lot, remaining_move_raws_without_finished_lot

	def get_components_remaining_quantity(self, splitted_qty, all_moves):
		component_remaining_qty = dict.fromkeys(self.move_raw_ids.mapped('product_id'), 0)
		factor = self.product_uom_id._compute_quantity(splitted_qty,
													   self.bom_id.product_uom_id) / self.bom_id.product_qty
		boms, lines = self.bom_id.explode(self.product_id, factor,
										  picking_type=self.bom_id.picking_type_id)
		for line in zip(list(map(lambda x: x[0].product_id, lines)), list(map(lambda x:x[1]['qty'], lines))):
			component_remaining_qty[line[0]] = line[1] - sum(all_moves.filtered(lambda move: move.product_id == line[
				0]).mapped('quantity_done'))
		return component_remaining_qty

	def manage_lots_on_workorder(self, finished_lots, new_wo, old_wo):
		old_wo.mo_serial_number_ids.filtered(
			lambda ms: ms.lot_id.id in finished_lots.ids).write({
				'workorder_id': new_wo.id,
				'production_id': new_wo.production_id.id,
			})
		if old_wo.mo_serial_number_ids:
			old_wo.mo_serial_number_ids[0].status = 'ready' if old_wo.state in ['ready', 'progress'] else 'pending'
			old_wo.finished_lot_id = old_wo.mo_serial_number_ids[0].lot_id.id

	def with_backflushing_splitting_mo(self, splitted_mo, finished_lots, remove_assembly=False):
		if splitted_mo:
			if remove_assembly:
				splitted_mo._onchange_move_raw()
			self.update_backflushing_moves(splitted_mo, finished_lots)
			self.create_workorder_for_new_mo(splitted_mo=splitted_mo, finished_lots=finished_lots, backflushing=True)
			return True

	def is_serial(self):
		return self.finished_product_tracking == 'serial'

	def reverse_moves(self, moves, move_vals, reference):
		reversed_moves = self.env['stock.move']
		for move_id in moves:
			move_vals.update({
				'name': 'Reversed Move' + ' - %s' % reference if reference else '',
				'location_id': move_id.location_dest_id.id,
				'location_dest_id': move_id.location_id.id,
				'reference': reference,
				'product_uom_qty': move_id.product_uom_qty,
			})
			reversed_move_id = move_id.copy(move_vals)
			reversed_move_id._action_confirm()
			reversed_move_id._action_assign()
			# Update move lines and set lot in it
			for old_ml, new_ml in zip(move_id.move_line_ids, reversed_move_id.move_line_ids):
				new_ml.write({
					'lot_id': old_ml.lot_id.id,
				})
			reversed_move_id._set_quantity_done(move_id.quantity_done)
			reversed_move_id._action_done()
			reversed_moves |= reversed_move_id
		return reversed_moves

	def get_splitted_mo(self, finished_lots, splitted_qty):
		new_moves = self.env['stock.move']
		new_move_lines = self.env['stock.move.line']
		extra_move_line = self.env['stock.move.line']
		move_raws_with_finished_lot, remaining_move_raws_without_finished_lot = self.get_move_raws(finished_lots=finished_lots)
		backflushed_picking = self.backflush_on_mo_completion
		final_splitted_qty = 1 if backflushed_picking else splitted_qty
		components_remaining_quantity = self.get_components_remaining_quantity(
			splitted_qty, move_raws_with_finished_lot+remaining_move_raws_without_finished_lot)
		for move in list(list(set(move_raws_with_finished_lot))):
			new_move_id = move.copy({'product_uom_qty': final_splitted_qty,
									 'quantity_done': move.quantity_done,
									 'reference_move_of_original_component_id': move.id,
									 'state': 'confirmed'})
			# need_to_del_ml = new_move_id.move_line_ids
			new_moves += new_move_id
			new_move_id.with_context(do_not_unreserve=True).write({'quantity_done': 0, 'reserved_availability': 0})

			if not backflushed_picking:
				move.write({'product_uom_qty': move.product_uom_qty - splitted_qty})
			self.reverse_moves(
				moves= move,
				move_vals={'raw_material_production_id': False, 'production_id': False,
						   'picking_type_id': False, 'picking_id': False},
				reference=self.name,
			)
			# We are setting the new move done because it is already done in old MO
			# new_move_id._action_assign()
			# Update move lines and set lot in it
			# new_move_id._action_confirm()
			# new_move_id._action_assign()
			for old_ml, new_ml in zip(move.move_line_ids, new_move_id.move_line_ids):
				new_ml.write({
					'lot_id': old_ml.lot_id.id,
					'lot_produced_ids': [(6, 0, old_ml.lot_produced_ids.ids)],
					'product_uom_qty': old_ml.product_uom_qty,
					'qty_done': old_ml.qty_done,
				})
				new_move_lines += new_ml
			new_move_id._action_done()

		for move in remaining_move_raws_without_finished_lot:
			new_move_id = move.copy({'product_uom_qty': components_remaining_quantity[move.product_id],
									 'reference_move_of_original_component_id': move.id})
			new_moves += new_move_id
			for move_line in move.move_line_ids:
				new_move_lines += move_line.copy({'move_id': new_move_id.id, 'qty_done': 0,
												  'product_uom_qty': 0})

			move.with_context(do_not_unreserve=True).write(
				{'product_uom_qty': move.product_uom_qty - components_remaining_quantity[move.product_id],})
			new_move_id.with_context(do_not_unreserve=True).write({'reserved_availability': 0})
		splitted_mo = self.copy({'move_raw_ids': [(6, 0, new_moves.ids)],
								 'product_qty': splitted_qty,
								 'split_order_source_id': self.id,
								 'state': 'progress'})
		splitted_mo.write({'state': 'progress'})
		return splitted_mo, new_moves, new_move_lines

	def manage_work_orders(self, splitted_mo, finished_lots, new_moves, new_move_lines):
		for wo in self.workorder_ids:
			finished_wo_lines = self.env['mrp.workorder.line']
			wo_finished_lots = wo.finished_workorder_line_ids.mapped('lot_id.id')
			finished_line_ids = wo.finished_workorder_line_ids.filtered(lambda f: f.lot_id.id in finished_lots.ids)
			for wo_line in finished_line_ids:
				finished_wo_lines |= wo_line.copy({'move_id': splitted_mo.move_raw_ids.filtered(
					lambda mr: mr.reference_move_of_original_component_id.id == wo_line.move_id.id).id,})
			new_wo = wo.copy({
				'production_id': splitted_mo.id,
				'state': wo.state,
				'qty_produced': len(finished_wo_lines),
				'finished_workorder_line_ids': [(6, 0, finished_wo_lines.ids)],
				'next_work_order_id': False,
				'component_qty_to_do': 0.0,
			})
			# Need to unlink from old WO, as we don't require after split
			finished_line_ids.unlink()

			if finished_wo_lines.mapped('lot_id.id') == finished_lots.ids:
				new_wo.state = 'done'
				# Update finished lot number in new workorder
				new_wo.finished_lot_id = finished_lots[-1].id
			else:
				finished_lot_id = finished_lots - finished_wo_lines.mapped('lot_id')
				if finished_lot_id:
					new_wo.finished_lot_id = finished_lot_id[0].id
			move = new_moves.filtered(lambda x: x.workorder_id == wo)
			move_line = new_move_lines.filtered(lambda x: x.workorder_id == wo)
			move.write({'workorder_id': new_wo.id})
			# wo.raw_workorder_line_ids.write({'move_id': move.id})
			# TODO: commented below line for merging with backflush and splitting
			# finished_line_ids.write({'move_id': move.id})
			move_line.write({'workorder_id': new_wo.id})
			# Update OLD MO work order with WO line and Qty Produced.
			wo.write({'qty_produced': len(wo.finished_workorder_line_ids), 'qty_done': 0})
			wo._refresh_wo_lines()
			new_wo._generate_wo_lines()

			wo._compute_component_data()
			self.manage_checks(wo, new_wo, finished_lots)
			self.manage_lots_on_workorder(finished_lots, new_wo=new_wo, old_wo=wo)

		workorder_ids = splitted_mo.workorder_ids.ids
		for index, wo in enumerate(workorder_ids):
			if index == len(workorder_ids) - 1:
				break
			else:
				splitted_mo.workorder_ids.filtered(lambda w: w.id == wo).with_context(force=True).write({
					'next_work_order_id': workorder_ids[index + 1]
				})
		done_workorder = splitted_mo.workorder_ids.filtered(lambda w: w.state == 'done')
		not_done_workorder = splitted_mo.workorder_ids - done_workorder
		if not_done_workorder and not_done_workorder[0].state == 'pending':
			not_done_workorder[0].write({'state': 'ready'})
		done_workorder.mapped('raw_workorder_line_ids').unlink()
		done_workorder.write({'qty_done': 0, 'component_remaining_qty': 0, 'current_quality_check_id': False,
							  'workorder_line_id': False, 'qty_producing': 0})
		(splitted_mo.workorder_ids - done_workorder).write({
			'component_remaining_qty': 1
		})
		# Reassigning moves from old MO
		self.mapped('move_raw_ids').filtered(lambda m: m.state not in ['cancel', 'done'])._do_unreserve()
		self.action_assign()

	# Splitting MO for bad quality lots
	def button_mo_split(self, finished_lots, remove_assembly=False):
		self.check_splits_allowed()
		if self.is_serial():
			splitted_qty = len(finished_lots)
			self.product_qty -= splitted_qty
			splitted_mo, new_moves, new_move_lines = self.get_splitted_mo(finished_lots=finished_lots,
																		  splitted_qty=splitted_qty)
			if not self.backflush_on_mo_completion:
				splitted_mo._onchange_move_raw()
			# splitted_mo.action_confirm()
			splitted_finished_moves = splitted_mo._generate_finished_moves()
			splitted_finished_moves._action_confirm()
			splitted_mo.write({'state': 'progress'})
			self.manage_work_orders(splitted_mo, finished_lots, new_moves, new_move_lines)
		return True

	def write(self, vals):
		if vals and vals.get('date_planned_finished', False):
			components_lot_ids = self.move_raw_ids.mapped('move_line_ids')
			for component_lot in zip(components_lot_ids.mapped('lot_id'), components_lot_ids.mapped('location_dest_id')):
				component_lot[0].calculate_lot_status(location_id=component_lot[1].id, operation_type='add')
		return super(MrpProduction, self).write(vals)

	# Resetting workorders
	def reset_workorders(self, product_ids=False):
		if not product_ids:
			return True
		# Matched workorder ines
		matched_workorder_lines = self.workorder_ids.mapped('raw_workorder_line_ids').filtered(
			lambda wl: wl.product_id.id in product_ids)
		# Remove finished step associated with the component and matched WL lines
		matched_workorder_lines.mapped('check_ids').unlink()
		matched_workorder_lines.unlink()
