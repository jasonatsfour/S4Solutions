odoo.define('as_built_report_base.autofold', function (require) {

"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var session = require('web.session');
var framework = require('web.framework');
var stock_report_generic = require('stock.stock_report_generic');
var QWeb = core.qweb;
var rpc = require('web.rpc')
var Dialog = require('web.Dialog');
var _t = core._t;
var deferred = $.Deferred();
var report_widget = require('stock.ReportWidget')

report_widget.include({

    autounfold: function(target, lot_name) {
        var self = this;
        var $CurretElement;
        $CurretElement = $(target).parents('tr').find('td.o_stock_reports_unfoldable');
        var active_id = $CurretElement.data('id');
        var active_model_name = $CurretElement.data('model');
        var active_model_id = $CurretElement.data('model_id');
        var row_level = $CurretElement.data('level');
        var $cursor = $(target).parents('tr');
        this._rpc({
                model: 'stock.traceability.report',
                method: 'get_lines',
                args: [parseInt(active_id, 10)],
                kwargs: {
                    'model_id': active_model_id,
                    'model_name': active_model_name,
                    'level': parseInt(row_level) + 30 || 1
                },
            })
            .then(function (lines) {// After loading the line
               _.each(lines, function (line) { // Render each line
                    $cursor.after(QWeb.render("report_mrp_line", {l: line}));
                    $cursor = $cursor.next();
                    if (line.inventory_adj == true)
                    {
                        $cursor.addClass('o_class_hidden')
                    }
                    if ($(target).hasClass('lot_nu')){
                        if (line.lot_name == false)
                        {
                            $cursor.addClass('o_class_hidden')
                        }
                        else{
                            $cursor.addClass('Lot_no')
                        }
                    }
                    if (line.usage == 'in'){
                        $cursor.addClass('inv_prod')
                    }
                    });
                });
        $CurretElement.attr('class', 'o_stock_reports_foldable ' + active_id); // Change the class, and rendering of the unfolded line
        $(target).parents('tr').find('span.o_stock_reports_unfoldable').replaceWith(QWeb.render("foldable", {lineId: active_id}));
        $(target).parents('tr').toggleClass('o_stock_reports_unfolded');
    },
});
})
