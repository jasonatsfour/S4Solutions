odoo.define('zipline_barcode_enhancements.stock_barcode', function (require) {
"use strict";
	var LinesWidget = require('stock_barcode.LinesWidget');
	LinesWidget.include({
		events: _.extend({}, LinesWidget.prototype.events, {
            'click .o_add_line_qty': '_onClickAddLineQty',
            'click .o_new_validate_page': '_onClickNewValidatePage',
        }),

		_onClickAddLineQty: function (ev) {
        	ev.stopPropagation();
        	var product_input_fields = $("[id^='move-product-qty-']");
	        var i;
	        for (i=0; i < product_input_fields.length; i++) {
	        	var move_line_id = product_input_fields[i].id.split("-").slice(-1).pop();
	        	var prod_qty = product_input_fields[i].value;
	        	this._rpc({
		            model: 'stock.move.line',
		            method: 'get_update_quantity',
		            args: [product_input_fields[i].id, move_line_id, prod_qty]
		        }).then(function (data){
		        	$('#' + move_line_id).load('#' + move_line_id);
		        	$(data['class']).html(data['html']);
		        	$(data['message']).html(data['message_html']);
		        });	
	        }
        },
        _onClickNewValidatePage: function (ev) {
        	ev.stopPropagation();
        	var product_input_fields = $("[id^='move-product-qty-']");
	        var i;
	        var is_valid = 1;
	        var self = this;
	        for (i=0; i < product_input_fields.length; i++) {
	        	var move_line_id = product_input_fields[i].id.split("-").slice(-1).pop();
	        	var prod_qty = product_input_fields[i].value;
	        	this._rpc({
		            model: 'stock.move.line',
		            method: 'get_update_quantity',
		            args: [product_input_fields[i].id, move_line_id, prod_qty]
		        }).then(function (data){
		        	if (data['is_qty_more'] === true){
		        		is_valid = 0
		        	}
		        	$('#' + move_line_id).load('#' + move_line_id);
		        	$(data['class']).html(data['html']);
		        	$(data['message']).html(data['message_html']);
		        });
	        }
	        setTimeout(function(){
	        	if (is_valid === 1){
	        		self._onClickValidatePage(ev)
	        	}}, 2000);	        
        }
	});
});