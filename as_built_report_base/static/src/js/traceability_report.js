odoo.define('as_built_report_base.ReportWidget', function (require) {
'use strict';

var core = require('web.core');
var Widget = require('web.Widget');
var AbstractAction = require('web.AbstractAction');
var QWeb = core.qweb;
var _t = core._t;

var ReportWidget = Widget.include({
    events: {
        'click .o_stock_reports_stream': 'updownStream',
        'click .o_stock_report_lot_action': 'actionOpenLot'
    },
   
    actionOpenLot: function(e) {
        e.preventDefault();
        var $el = $(e.target).parents('tr');
        var id = $($el[0]).attr('data-lot_id')
        this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'stock.production.lot',
                res_id: parseInt(id),
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'current'
            });
    },
    updownStream: function(e) {
        var $el = $(e.target).parents('tr');
        this.do_action({
            type: "ir.actions.client",
            tag: 'stock_report_generic',
            name: _t("As-Built Traceability Report"),
            context: {
                active_id : $el.data('model_id'),
                active_model : $el.data('model'),
                auto_unfold: true,
                lot_name: $el.data('lot_name') !== undefined && $el.data('lot_name').toString(),
                url: '/stock/output_format/stock/active_id'
            },
        });
    },
        
})

});
