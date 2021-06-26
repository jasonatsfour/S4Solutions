odoo.define('as_built_report_base.update_as_built_button', function (require) {
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

stock_report_generic.include({
    renderButtons: function() {
        var self = this;
        this.$buttons = $(QWeb.render("stockReports.buttons", {}));
            // pdf output
            this.$buttons.filter('.o_stock-widget-pdf').on('click', function(e) {
                var $element = $(self.$el[0]).find('.o_stock_reports_table tbody tr');
                var dict = [];
                $element.each(function( index ) {
                var mo = $($element[index].cells[1]).attr('data-res-model')
                var lot  = $($element[index].cells[2]).attr('data-lot_name')
                var $el = $($element[index]);
                    if (! $el.hasClass('o_class_hidden')) //manufactureing report
                    {
                    dict.push({
                            'id': $el.data('id'),
                            'model_id': $el.data('model_id'),
                            'model_name': $el.data('model'),
                            'unfoldable': $el.data('unfold'),
                            'level': $el.find('td:first').data('level') || 1
                    });
                }
                });
                framework.blockUI();
                var url_data = self.controller_url.replace('active_id', self.given_context.active_id);
                session.get_file({
                    url: url_data.replace('output_format', 'pdf'),
                    data: {data: JSON.stringify(dict)},
                    complete: framework.unblockUI,
                    error: (error) => self.call('crash_manager', 'rpc_error', error),
                });
            });
        // show and hide records in traceability report
        // Show Good Movements
        // var a = this.$buttons.find('.o_button_expand');
        this.$buttons.filter('.o_button_expand').on('click', function(e) {

            var $element = $(self.$el[0]).find('.o_stock_reports_table tbody tr');
            var table_length = $element.length;
            var check_expendex_length = 0
            var unfoldable_btn_length = $element.find('td.o_stock_reports_unfoldable .o_stock_reports_unfoldable').length;
            var table_expanded = false;
            loop_rows($element);
            function loop_rows($table){
                check_expendex_length = $table.length
                $table.each(function( index ) {
                    var $el = $($table[index]);
                    manage_row_expension($el)
                })
                if(table_expanded)
                {
                    table_expanded = false;
                    manage_row_timeout();
                    function manage_row_timeout(){
                        var execute_row_timeout;
                        clearTimeout(execute_row_timeout);
                        execute_row_timeout = setTimeout(function(){
                            var current_tbl_length = $(self.$el[0]).find('.o_stock_reports_table tbody tr').length;
                            if(current_tbl_length <= check_expendex_length)
                            {
                                manage_row_timeout();
                            }
                            else
                            {
                                loop_rows($(self.$el[0]).find('.o_stock_reports_table tbody tr'))
                            }
                        }, 200);
                    }
                }
                else
                {
                    manage_hide_show();
                }

            }
            function manage_row_expension($element){
                var $el = $element;
                var parent_length = $el.parent().find('tr').length;
                self.$CurretElement = $el.find('td.o_stock_reports_unfoldable .o_stock_reports_unfoldable')
                if(self.$CurretElement.length)
                {
                    self.$CurretElement.click()
                    table_expanded = true
                }
            }
            function manage_hide_show(){
                if(table_length == unfoldable_btn_length)
                {
                    var new_table_length = $(self.$el[0]).find('.o_stock_reports_table tbody tr').length;
                    manage_timeout();
                    function manage_timeout(){
                        var execute_timeout;
                        clearTimeout(execute_timeout);
                        execute_timeout = setTimeout(function(){
                            new_table_length = $(self.$el[0]).find('.o_stock_reports_table tbody tr').length;
                            if(new_table_length <= table_length)
                            {
                                manage_timeout();
                            }
                            else
                            {
                                toggle_visible();
                            }
                        }, 200);
                    }
                }
                else
                {
                    toggle_visible();
                }
            }
            function toggle_visible(){
                var $inner_element = $(self.$el[0]).find('.o_stock_reports_table tbody tr');
                $inner_element.each(function( index ) {
                    var $el = $($inner_element[index]);
                    $el.removeAttr('style');
                    if($el.hasClass('o_class_hidden')){
                        $el.removeClass('o_class_hidden')
                        $el.addClass('o_class_hide_click')
                    }
                });
            }
            self.$('.o_button_expand').hide();
            self.$('#hide_goods_movement').removeClass('o_button_compose');
        })
        this.$buttons.filter('.o_button_compose').on('click', function(e) {
            var $element = $(self.$el[0]).find('.o_stock_reports_table tbody tr');
            for (var i = 0; i < $element.length; i++) {
                var res_model = $($element[i]).attr('data-res-model')
                var unfold = $($element[i]).attr('data-unfold')
                var hide = $($element[i]).hasClass('o_class_hide_click')
                if (hide && !$($element[i]).hasClass('production_lot'))
                {
                    $($element[i]).addClass('o_class_hidden')
                    $($element[i]).removeClass('o_class_hide_click')
                }
                else{
                    $($element[i]).removeClass('o_class_hidden')
                }
                if (res_model == 'stock.inventory')
                {
                    $($element[i]).addClass('o_class_hidden')
                }
                if ($($element[i]).hasClass('inv_prod')){
                    $($element[i]).addClass('o_class_hidden')
                }
            }

            self.$('#hide_goods_movement').addClass('o_button_compose');
            self.$('.o_button_expand').show();
        })
         this.$buttons.filter('.o_button_expand_lot').on('click', function(e) {
            var $element = $(self.$el[0]).find('.o_stock_reports_table tbody tr');
            var table_length = $element.length;
            var check_expendex_length = 0
            var unfoldable_btn_lot_length = $element.find('td.o_stock_reports_unfoldable .o_stock_reports_unfoldable').length;
            var table_expanded_lot = false;
            loop_rows_lot($element);
            function loop_rows_lot($table){
                check_expendex_length = $table.length
                $table.each(function( index ) {
                    var $el = $($table[index]);
                    manage_row_expension_lot($el)
                })
            }
            function manage_row_expension_lot($element){
                var $el = $element;
                var parent_length = $el.parent().find('tr').length;
                self.$CurretElement = $el.find('td.o_stock_reports_unfoldable .o_stock_reports_unfoldable')
                self.$CurretElement.addClass('lot_nu')
                if(self.$CurretElement.length)
                {
                    self.$CurretElement.click()
                    table_expanded_lot = true
                }

                if(table_expanded_lot)
                {
                    table_expanded_lot = false;
                    manage_row_timeout_lot();
                    function manage_row_timeout_lot(){
                        var execute_row_timeout;
                        clearTimeout(execute_row_timeout);
                        execute_row_timeout = setTimeout(function(){
                            var current_tbl_length = $(self.$el[0]).find('.o_stock_reports_table tbody tr').length;
                            if(current_tbl_length <= check_expendex_length)
                            {
                                manage_row_timeout_lot();
                            }
                            else
                            {
                                loop_rows_lot($(self.$el[0]).find('.o_stock_reports_table tbody tr'))
                            }
                        }, 200);
                    }
                }
                else
                {
                    manage_hide_show_lot();
                }
            }
            function manage_hide_show_lot(){
                if(table_length == unfoldable_btn_lot_length)
                {
                    var new_table_length = $(self.$el[0]).find('.o_stock_reports_table tbody tr').length;
                    manage_timeout_lot();
                    function manage_timeout_lot(){
                        var execute_timeout;
                        clearTimeout(execute_timeout);
                        execute_timeout = setTimeout(function(){
                            new_table_length = $(self.$el[0]).find('.o_stock_reports_table tbody tr').length;
                            if(new_table_length <= table_length)
                            {
                                manage_timeout_lot();
                            }
                            else
                            {
                                toggle_visible_lot();
                            }
                        }, 200);
                    }
                }
                else
                {
                    toggle_visible_lot();
                }
            }
            function toggle_visible_lot(){
                var $inner_element = $(self.$el[0]).find('.o_stock_reports_table tbody tr');
                $inner_element.each(function( index ) {
                    var $el = $($inner_element[index]);
                    if ($el[0].dataset.lot_name == 'false'){
                        $el.addClass('o_class_hidden production_lot')
                    }
                    if($el.hasClass('o_class_hidden') && $el.hasClass('Lot_no')){
                        $el.removeAttr('style');
                        $el.removeClass('o_class_hidden')
                        $el.addClass('o_class_hide_click')
                    }
                });
            }
        })
        return this.$buttons;
    }
})
});
