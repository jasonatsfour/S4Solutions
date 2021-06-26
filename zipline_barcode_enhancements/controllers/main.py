# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.stock_barcode.controllers.main import StockBarcodeController
from odoo.exceptions import ValidationError, UserError
import werkzeug.utils


class StockBarcodeController(StockBarcodeController):

	@http.route(['/product-quntity-update'], type='http', auth="public", methods=['POST'], website=True, csrf=False)
	def product_qty_update(self, **kw):
		quantity = kw['quantity'] and float(kw['quantity']) or 0.0
		action_id = request.env['ir.actions.client'].sudo().search([('tag', '=', 'stock_barcode_picking_client_action')])
		move_line_ids = request.env['stock.move.line'].sudo().browse(int(kw['move_line_id']))
		demand_qty = move_line_ids.move_id.product_uom_qty or 0.0
		update_qty = quantity
		total_updated_qty = 0.0
		for line in move_line_ids.move_id.move_line_ids:
			if line.id == move_line_ids.id:
				continue
			total_updated_qty += line.qty_done
		total_updated_qty += quantity
		if demand_qty < total_updated_qty:
			update_qty = 0.0
			move_line_ids.barcode_msg = "You have added more quantity than demanded"
			move_line_ids.is_exception = True
		else:
			move_line_ids.barcode_msg = "Quantity is updated"
			move_line_ids.is_exception = False
		move_line_ids.qty_done = update_qty
		menu_id = request.env.ref('stock_barcode.stock_barcode_menu')
		url = "web#action=%s&active_id=%s&menu_id=%s" % (action_id.id, move_line_ids[0].picking_id.id, menu_id.id)
		return werkzeug.utils.redirect(url)
