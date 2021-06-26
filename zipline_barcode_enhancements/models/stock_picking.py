# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockMoveLine(models.Model):
	_inherit = "stock.move.line"

	@api.model
	def get_update_quantity(self, input_id, move_line_id, qty):
		move_line_ids = self.env['stock.move.line'].sudo().browse(int(move_line_id))
		quantity = int(qty)
		update_qty = int(qty)
		is_qty_more = False
		total_updated_qty = 0.0
		demand_qty = move_line_ids.move_id.product_uom_qty or 0.0
		for line in move_line_ids.move_id.move_line_ids:
			if line.id == move_line_ids.id:
				continue
			total_updated_qty += line.qty_done
		total_updated_qty += quantity
		msg = ""
		if demand_qty < total_updated_qty:
			update_qty = 0.0
			is_qty_more = True
			move_line_ids.barcode_msg = "You have added more quantity than demanded"
			msg = "You have added more quantity than demanded"
			move_line_ids.is_exception = True
		else:
			move_line_ids.barcode_msg = "Quantity is updated"
			move_line_ids.is_exception = False
		move_line_ids.qty_done = update_qty
		if msg:
			msg_html = '<h3><span class="text-danger" style="margin-right:5px;">%s</span></h3>' % msg
		else:
			msg_html = ''
		return {
			'class': '#line-qty-%s' % move_line_id,
			'value': move_line_ids.qty_done,
			'message':'#lot-msg-%s' % move_line_id, 
			'message_html': msg_html,
			'is_qty_more':is_qty_more,
			'html': '<span class="qty-done d-inline-block text-left">%s</span><span t-if="line.product_uom_qty">%s</span>' % (int(move_line_ids.qty_done), '/ ' + str(int(move_line_ids.product_uom_qty)))
		}


class StockPickingType(models.Model):
	_inherit = "stock.picking.type"

	force_scan = fields.Boolean(string="Force Scan the product",copy=False)

class StockPicking(models.Model):
	_inherit = "stock.picking"

	order_scanned = fields.Boolean(string="Force Scan The Product",copy=False)
	# location_id = fields.Many2one(
	# 	'stock.location', "Source Location",
	# 	default=lambda self: self.env['stock.picking.type'].browse(
	# 		self._context.get('default_picking_type_id')).default_location_src_id,
	# 	check_company=True, readonly=True, required=True,
	# 	states={'draft': [('readonly', False)], 'waiting': [('readonly', False)], 'confirmed': [('readonly', False)], 'assigned': [('readonly', False)]})

	# Function For JS to update the order scanned field
	@api.model
	def update_stock_scanned(self,picking_ids):
		for picking in picking_ids:
			picking_id = self.env['stock.picking'].sudo().browse(int(picking))
			if picking_id:
				picking_id.order_scanned = True
		return True

	def button_validate(self):
		picking_type_id = self.env['stock.picking.type'].search([('code','=','internal')])
		if picking_type_id:
			picking_type_id = picking_type_id[0]
		if self.picking_type_id.id == picking_type_id.id and self.picking_type_id.force_scan == True:
			if self.order_scanned == False:
				raise UserError(_("You must have to scan the source location before validate."))				
		return super(StockPicking,self).button_validate()

	def get_update_source_location(self, active_ids, barcode):
		location_ids = self.env['stock.location'].search([('barcode', '=', barcode)])
		current_location_id = {}
		is_update = 0
		if location_ids:
			current_location_id = {
				'id': location_ids[0].id,
				'display_name': location_ids[0].display_name,
				'parent_path': location_ids[0].parent_path
			}
			for active_id in active_ids:
				picking = self.env['stock.picking'].browse(active_id)
				if picking.picking_type_id.code == 'internal':
					is_update = 1
					picking.location_id = location_ids[0].id
					for line in picking.move_line_ids_without_package:
						line.location_id = location_ids[0].id
					picking.action_assign()
		current_location_id.update({
			'is_update': is_update
		})
		return current_location_id


	# def get_update_source_location(self, active_ids, barcode):
	# 	location_ids = self.env['stock.location'].search([('barcode', '=', barcode)])
	# 	current_location_id = {}
	# 	if location_ids:
	# 		current_location_id = {
	# 			'id': location_ids[0].id,
	# 			'display_name': location_ids[0].display_name,
	# 			'parent_path': location_ids[0].parent_path
	# 		}
	# 		for active_id in active_ids:
	# 			picking = self.env['stock.picking'].browse(active_id)
	# 			picking.location_id = location_ids[0].id
	# 			for line in picking.move_line_ids_without_package:
	# 				line.location_id = location_ids[0].id
	# 	return current_location_id
