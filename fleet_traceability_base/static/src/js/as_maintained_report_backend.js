odoo.define('fleet_traceability_base.as_maintained_report_generic', function (require) {
'use strict';

var core = require('web.core');
var AbstractAction = require('web.AbstractAction');
var session = require('web.session');
var Dialog = require('web.Dialog');
var ajax = require('web.ajax');
var ViewDialogs = require('web.view_dialogs');
var QWeb = core.qweb;
var _t = core._t;

window.all_row_rec = [];

var AsMaintainedReport = AbstractAction.extend({
    hasControlPanel: true,
    template: 'AsMaintainedReport',

    events: {
        'click span.o_stock_reports_foldable': 'folded',
        'click span.o_stock_reports_unfoldable': 'unfolded',
        'click span.report_plus_button': 'add_button',
        'click span.report_edit_button': 'edit_button',
        'click span.report_minus_button': 'remove_button',
        'click #expand_button': 'expand',
        'click #button_collapse': 'collapse',
        'click [action]': 'open_lot_record',
    },

    init: function(parent, action) {
        this.actionManager = parent;
        this.given_context = session.user_context;
        if (action.context.active_model){
            localStorage.setItem("active_model", action.context.active_model);
        }
        this.controller_url = action.context.url;
        if (action.context.context) {
            this.given_context = action.context.context;
        }
        this.given_context.active_id = action.context.active_id || action.params.active_id;
        this.given_context.model = localStorage.getItem("active_model") || false;
        this.given_context.ttype = action.context.ttype || false;
        return this._super.apply(this, arguments);
    },

    start: function() {
        var self = this;
        this._rpc({
            model: 'stock.production.lot',
            method: 'get_lot_serial_number',
            args: [self.given_context],
            context: self.context
        }).then(function (data){
            $('.as_maintained_table tbody').append(
                '<tr data-row-lot-id="'+ data.lot_id + '">' +
                '<td><span class="o_stock_reports_unfoldable o_stock_reports_caret_icon ml16" level="1">' +
                '<i class="fa fa-fw fa-caret-right custom_fold_unfold"></i>' +
                '<a action="open_lot_record" href="#" data-lot-id="'+ data.lot_id + '">' + data.lot_number +
                '</a></span></td><td class="o_report_line_header"><span>' + data.internal_reference +
                '</span></td><td class="o_report_line_header"><span>' + data.product +
                '</span></td><td class="o_report_line_header product_id"><span>' + data.product_id +
                '</span></td><td class="o_report_line_header"><span>' + data.lot_version +
                '</span></td><td class="o_report_line_header"><span class="report_plus_button"><i class="add_button">Add</i></span></td></tr>')
            if (data.is_as_maintained_user == false){
                //if current user have not access for as-maintained structure configuration
                $('.as_maintained_table tbody').find('span.report_plus_button').hide()
            }
            $('#button_collapse').hide()
        });
    },

    removeLine: function(element) {
        var lot_number = [];
        lot_number.push(element.data('row-lot-id'))
        var current_level = element.nextAll('tr')
        _.each(current_level, function(level) {
            for(var lot in lot_number) {
                var parent_lot_rec = $('.as_maintained_table').find("[parent_lot_id='"+ lot_number[lot] + "']");
                if(parent_lot_rec.length) {
                    for(var j = 0; j < parent_lot_rec.length; j++) {
                        if(lot_number.indexOf($(parent_lot_rec[j]).data('row-lot-id')) == -1){
                            lot_number.push($(parent_lot_rec[j]).data('row-lot-id'))
                        }
                    }
                }
            }
        });
        for (var i = 1; i < lot_number.length; i++) {
            for (var j =0; j < current_level.length; j++) {
                if ($(current_level[j]).data('row-lot-id') == lot_number[i]) {
                    $(current_level[j]).remove()
                }
            }
        }
        element.find('span.o_stock_reports_foldable')
            .attr('class', 'o_stock_reports_unfoldable o_stock_reports_caret_icon');
    },

    folded: function(e) {
        this.removeLine($(e.target).parents('tr'));
        $(e.target)
            .parents('tr')
            .find('i.custom_fold_unfold')
            .replaceWith("<i class='fa fa-fw fa-caret-right custom_fold_unfold'></i>");
    },

    unfolded: function(e) {
        var current_row = $(e.target).parents('tr')
        var $CurretElement = $(e.target).parents('tr').find('span.o_stock_reports_unfoldable')
        var current_row = $(e.target).parents('tr')
        var level = $(e.target).parents('tr').find('span.o_stock_reports_caret_icon')
        $(e.target).parents('tr').find('i.custom_fold_unfold').replaceWith("<i class='fa fa-fw fa-caret-down custom_fold_unfold'></i>");
        var lot_number = current_row.data('row-lot-id')
        var product_id = $($(e)[0].currentTarget).parents('tr').find('.product_id').find('span').text()
        this._rpc({
            model: 'stock.production.lot',
            method: 'get_lot_lines',
            args: [parseInt(lot_number),parseInt(product_id)],
        })
        .then(function (lines) {// After loading the line
            var line;
            if (lines.length){
                for (line in lines) { // Render each line
                    var parent_level = parseInt(level.attr('level'))
                    var current_level = parent_level + 1;
                    var previous_level_margin = parseInt($CurretElement.css('marginLeft').replace(/[a-z]/gi, ''))
                    var current_level_margin = previous_level_margin + 16
                    var present_current_row = $(
                        '<tr parent_product_id="' + lines[line].parent_product_id + '" parent_lot_id="' + lines[line].parent_lot_id + '" data-row-lot-id="'+ lines[line].lot_id +'"><td><span class="o_stock_reports_unfoldable o_stock_reports_caret_icon" level="' + current_level + '" style="margin-left:' + current_level_margin + 'px"><i class="fa fa-fw fa-caret-right custom_fold_unfold"></i><a action="open_lot_record" href="#" data-lot-id="'+ lines[line].lot_id + '" data-non-lot-id="'+ lines[line].non_lot_id + '">' + lines[line].lot_number +
                        '</a></span><input type="hidden" class="from-control lot_id" data-id="' + lines[line].parent_lot_id + '"></input></td><td class="o_report_line_header"><span>' + lines[line].internal_reference +
                        '</span></td><td class="o_report_line_header"><span>' + lines[line].product +
                        '</span></td><td class="o_report_line_header product_id"><span>' + lines[line].product_id +
                        '</span></td><td class="o_report_line_header"><span>' + lines[line].lot_version +
                        '</span></td><td class="o_report_line_header"><span class="report_plus_button"><i class="add_button">Add</i></span><span class="report_edit_button"><i class="edit_button">Edit</i></span><span class="report_minus_button"><i class="delete_button">Delete</i></span></td></tr>').insertAfter(current_row)
                    if (lines[line].is_as_maintained_user == false) {  //if current user have not access for as-maintained structure configuration
                        $('.as_maintained_table tbody').find('span.report_plus_button').hide()
                        $('.as_maintained_table tbody').find('span.report_edit_button').hide()
                        $('.as_maintained_table tbody').find('span.report_minus_button').hide()
                    }
                    if (lines[line].is_non_traceable == true) {  //if there is non-traceable lot, then hide add button
                        present_current_row.find('span.report_plus_button').hide()
                    }
                }
                $CurretElement.attr('class', 'o_stock_reports_foldable o_stock_reports_caret_icon')
                $CurretElement.css({marginLeft: previous_level_margin + "px"})
            }
            else {
                var previous_level_margin = parseInt($CurretElement.css('marginLeft').replace(/[a-z]/gi, ''))
                $CurretElement.attr('class', 'o_stock_reports_foldable o_stock_reports_caret_icon')
                $CurretElement.css({marginLeft: previous_level_margin + "px"})
            }
        });
    },

    setup_add_edit_component: function(e) {
        var button_call = $(this).find("input[type=radio]:checked").val()
        if (button_call == 'non_traceable') {
            $('#traceable_lot').hide()
            $('#non_traceable').show()
            // $('#non_traceable').select2();
            $('div[id$="traceable_lot"]').hide()
        }
        else if (button_call == 'traceable') {
            $('#non_traceable').hide()
            $('#traceable_lot').show()
            // $('#traceable_lot').select2();
            $('div[id$="non_traceable"]').hide()
        }
    },

    add_button : function(e){
        var self = this;
        var parent_lot_number = $(e.target).parents('tr').attr('parent_lot_id')
        var current_lot_number = $(e.target).parents('tr').data('row-lot-id')
        var product_id = $(e.target).parents('tr').find('.product_id').find('span').text()
        var operation;
        ajax.jsonRpc(
            "/get_serial_number_list",
            'call',
            {
                'parent_lot_number': parent_lot_number,
                'current_lot_number': current_lot_number,
                'product_id': parseInt(product_id)
            }
        ).then(function (modal) {
            var $modal = $(modal);
            $modal.modal('show');
            $modal.on('hidden.bs.modal', function () {
                $(this).remove();
            });

            // Initialize select2
            // $modal.find("#traceable_lot").select2();

            var field_selection_warning = $modal.find('#lot_ids').find(".form-group")
            field_selection_warning.find('.form-control-warning').hide()

            var non_traceable = $modal.find('#lot_ids').find(".form-group")
            non_traceable.find('#non_traceable').hide()
            $modal.on('click', '.js_goto_event', function () {
                e.preventDefault();
                $modal.modal('hide');
            });
            $modal.on('change', '#traceability', function(){
                self.setup_add_edit_component()
            });
            // open_lot_search_panel
            $modal.on('click', '.open_lot_search_panel', function(){
                // var self = this;
                var available_lot_status = $('#available_lot_status').val()
                var parent_lot_id = parseInt($('#parent_lot_id').val())
                new ViewDialogs.SelectCreateDialog(self, {
                    res_model: 'stock.production.lot',
                    domain: [
                        ['stock_production_lot_status_id', 'in', JSON.parse(available_lot_status)],
                        ['id', 'not in', [parent_lot_id]],
                        ['is_none_production', '=', false]
                    ],
                    title: _.str.sprintf(_t("Search: %s"), 'Lot Serial Number'),
                    no_create: false,
                    disable_multiple_selection: true,
                    // context: state.context,
                    on_selected: function (records) {
                        var lot_id = records[0]
                        self._rpc({
                            model: 'fleet.repair',
                            method: 'selected_lot_details',
                            args: [lot_id],
                        }).then(function (data) {
                            $('#new_selected_lot_id').val(lot_id['id']);
                            $('#traceable_lot_number').val(data.lot_name);
                        });
                    },
                }).open();
            });

            // open_non_lot_search_panel
            $modal.on('click', '.open_non_lot_search_panel', function(){
                new ViewDialogs.SelectCreateDialog(self, {
                    res_model: 'stock.production.quant',
                    title: _.str.sprintf(_t("Search: %s"), 'Non-Traceable Lot'),
                    no_create: false,
                    disable_multiple_selection: true,
                    on_selected: function (records) {
                        var lot_id = records[0]
                        self._rpc({
                            model: 'fleet.repair',
                            method: 'selected_non_lot_details',
                            args: [lot_id],
                        }).then(function (data) {
                            $('#non_traceable_lot_number').val(data.lot_name)
                        });
                    },
                }).open();
            });

            $modal.on('click', '.serial_number_add', function(){
                if ($("#traceable_lot_number").val() !== ""){
                    var selected_lot_number = $("#new_selected_lot_id").val();
                    var lot_details = {
                        'parent_lot_number': parseInt(current_lot_number),
                        'current_lot_number': parseInt(selected_lot_number),
                        'operation': 'add'
                    }
                    self._rpc({
                        model: 'fleet.repair',
                        method: 'add_remove_lot_serial_number',
                        args: [lot_details],
                    }).then(function (data) {
                        $modal.modal('hide');
                        if (data == 'no repair location') {
                            Dialog.alert(
                                self,
                                _t("No location is set while creating repair order. So please assign location on parent lot serial number."),
                                {title: _t('Warning'),}
                            );
                        }
                    })
                }
                else if($("#non_traceable_lot_number").val() !== "") {
                    var selected_non_traceable_lot = $("#non_traceable_lot_number").val();
                    var lot_details = {
                        'parent_lot_number': current_lot_number,
                        'current_lot_number': selected_non_traceable_lot,
                        'operation': 'add'
                    }
                    self._rpc({
                        model: 'fleet.repair',
                        method: 'add_remove_non_traceable_lot',
                        args: [lot_details],
                    }).then(function (data) {
                        $modal.modal('hide');
                        if (data == 'no repair location') {
                            Dialog.alert(
                                self,
                                _t("No location is set while creating repair order. So please assign location on parent lot serial number."),
                                {title: _t('Warning'),}
                            );
                        }
                    })
                }
                else {
                    field_selection_warning.find('.form-control-warning').show()
                }
            });
        });
    },

    edit_button : function(e){
        var self = this;
        var lot_number = $(e.target).parents('tr').data('row-lot-id');
        var parent_lot_number = parseInt($(e.target).parents('tr').attr('parent_lot_id'));
        var parent_product_id = $(e.target).parents('tr').attr('parent_product_id')
        var operation;
        ajax.jsonRpc(
            "/edit_lot_serial_number",
            'call',
            {
                'lot_number': lot_number,
                'parent_lot_number': parent_lot_number
            }
        ).then(function (modal) {
            var $modal = $(modal);
            $modal.modal('show');
            $modal.on('hidden.bs.modal', function () {
                $(this).remove();
            });

            // Initialize select2
            // $modal.find("#traceable_lot").select2();

            var field_selection_warning = $modal.find('#lot_ids').find(".form-group")
            field_selection_warning.find('.form-control-warning').hide()

            var non_traceable = $modal.find('#lot_ids').find(".form-group")
            non_traceable.find('#non_traceable').hide()
            $modal.on('click', '.js_goto_event', function () {
                e.preventDefault();
                $modal.modal('hide');
            });

            $modal.on('change', '#traceability', function(){
                self.setup_add_edit_component()
            });

            // open_lot_search_panel
            $modal.on('click', '.open_lot_search_panel', function(){
                var available_lot_status = $('#available_lot_status').val()
                new ViewDialogs.SelectCreateDialog(self, {
                    res_model: 'stock.production.lot',
                    domain: [
                        ['stock_production_lot_status_id', 'in', JSON.parse(available_lot_status)],
                        ['is_none_production', '=', false]
                    ],
                    title: _.str.sprintf(_t("Search: %s"), 'Lot Serial Number'),
                    no_create: false,
                    disable_multiple_selection: true,
                    on_selected: function (records) {
                        var lot_id = records[0]
                        self._rpc({
                            model: 'fleet.repair',
                            method: 'selected_lot_details',
                            args: [lot_id],
                        }).then(function (data) {
                            $('#traceable_lot_id').val(lot_id['id'])
                            $('#traceable_lot_number').val(data.lot_name)
                        });
                    },
                }).open();
            });

            // open_non_lot_search_panel
            $modal.on('click', '.open_non_lot_search_panel', function(){
                new ViewDialogs.SelectCreateDialog(self, {
                    res_model: 'stock.production.quant',
                    title: _.str.sprintf(_t("Search: %s"), 'Non-Traceable Lot'),
                    no_create: false,
                    disable_multiple_selection: true,
                    on_selected: function (records) {
                        var lot_id = records[0]
                        self._rpc({
                            model: 'fleet.repair',
                            method: 'selected_non_lot_details',
                            args: [lot_id],
                        }).then(function (data) {
                            $('#non_traceable_lot_number').val(data.lot_name)
                        });
                    },
                }).open();
            });

            $modal.on('click', '.serial_number_edit', function(){
                if ($("#traceable_lot_number").val() !== ""){
                    var selected_lot_number = parseInt($("#traceable_lot_id").val());
                    var lot_details = {
                        'parent_lot_number': parent_lot_number,
                        'parent_product_id': parseInt(parent_product_id),
                        'selected_lot_number': selected_lot_number,
                        'current_lot_number': lot_number,
                        'operation': 'edit'
                    }
                    self._rpc({
                        model: 'fleet.repair',
                        method: 'add_remove_lot_serial_number',
                        args: [lot_details],
                    }).then(function (data) {
                        $modal.modal('hide');
                        if (data == 'No repair location.') {
                            Dialog.alert(self, _t("No location is set while creating repair order. So please assign location on parent lot serial number."), {
                                title: _t('Warning'),
                            });
                        }
                        else if(data == 'not serial') {
                            Dialog.alert(self, _t("The product of selected lot number '" +  selected_lot_number + "' does not have any serialization traceability."), {
                                title: _t('Warning'),
                            });
                        }
                    })
                }
                else if($("#non_traceable_lot_number").val() !== "") {
                    var selected_non_traceable_lot = $("#non_traceable_lot_number").val();
                    var lot_details = {
                        'parent_lot_number': parent_lot_number,
                        'selected_lot_number': selected_non_traceable_lot,
                        'current_lot_number': lot_number,
                        'operation': 'edit'
                    }
                    self._rpc({
                        model: 'fleet.repair',
                        method: 'add_remove_non_traceable_lot',
                        args: [lot_details],
                    }).then(function (data) {
                        $modal.modal('hide');
                    })
                }
                else {
                    field_selection_warning.find('.form-control-warning').show()
                }
            });
        });
    },

    remove_button : function(e){
        var self = this;
        var lot_number = $(e.target).parents('tr').data('row-lot-id');
        var parent_lot_number = parseInt($(e.target).parents('tr').attr('parent_lot_id'));
        var parent_product_id = parseInt($(e.target).parents('tr').attr('parent_product_id'));
        ajax.jsonRpc('/remove_lot_serial_number',
            'call', {
                'lot_number': lot_number,
                'parent_lot_number': parent_lot_number
            }
        ).then(function (modal) {
            var $modal = $(modal);
            $modal.modal('show');
            $modal.on('hidden.bs.modal', function () {
                $(this).remove();
            });
            $modal.on('click', '.js_goto_event', function () {
                e.preventDefault();
                $modal.modal('hide');
            });
            $modal.on('click', '.serial_number_remove', function(){
                if($('#non_traceable').val()) {
                    var lot_details = {
                        'parent_lot_number': parent_lot_number,
                        'parent_product_id': parent_product_id,
                        'current_lot_number': lot_number,
                        'operation': 'remove'
                    }
                    self._rpc({
                        model: 'fleet.repair',
                        method: 'add_remove_non_traceable_lot',
                        args: [lot_details],
                    }).then(function (data) {
                        $modal.modal('hide');
                        if (data == 'No repair location.') {
                            Dialog.alert(
                                self,
                                _t('No location is set while creating repair order. So please assign location on parent lot serial number.'),
                                {title: _t('Warning')}
                            );
                        }
                    })
                }
                else {
                    var lot_details = {
                        'parent_lot_number': parent_lot_number,
                        'parent_product_id': parseInt(parent_product_id),
                        // 'selected_lot_number': selected_lot_number,
                        'current_lot_number': lot_number,
                        'operation': 'remove'
                    }
                    self._rpc({
                        model: 'fleet.repair',
                        method: 'add_remove_lot_serial_number',
                        args: [lot_details],
                    }).then(function (data) {
                        $modal.modal('hide');
                        if (data == 'No repair location.') {
                            Dialog.alert(self, _t("No location is set while creating repair order. So please assign location on parent lot serial number."), {
                                title: _t('Warning'),
                            });
                        }
                    })
                }
            });
        });
    },

    expand: function(e) {
        var self = this;
        var current_row = $($('.as_maintained_table tbody')[0]).find("tr:first")
        var $CurretElement = current_row.find('span.o_stock_reports_caret_icon')
        var level = $($('.as_maintained_table tbody')[0]).find('span.o_stock_reports_caret_icon')
        $($('.as_maintained_table tbody')[0])
            .find('i.custom_fold_unfold')
            .replaceWith("<i class='fa fa-fw fa-caret-down custom_fold_unfold'></i>");
        var lot_number = current_row.data('row-lot-id')
        var product_id = $($('.as_maintained_table tbody')[0])
            .find("tr:first")
            .find('.product_id')
            .find('span').text()
        $('#expand_button').hide()
        $('#button_collapse').show()
        this._rpc({
            model: 'stock.production.lot',
            method: 'get_all_lots',
            args: [lot_number, parseInt(product_id)],
            context: self.context
        }).then(function (lines){
            var existing_row = current_row.nextAll('tr')
            for (var i = 0; i < existing_row.length; i++) {
                $(existing_row[i]).remove()
            }
            if (lines != 'Not Exist.') {
                if (lines.length) {
                    // Render each line
                    for (var line in lines) {
                        var lot_rec = lines[line]
                        for (var lot in lot_rec) {
                            var previous_level_margin = parseInt($CurretElement.css('marginLeft').replace(/[a-z]/gi, ''))
                            var current_level_margin = lot_rec[lot].level * 16
                            if (lot_rec[lot].level > 2) {
                                var present_current_row = $('.as_maintained_table tbody')
                                    .find("[data-row-lot-id='"+ lot_rec[lot].parent_lot_id + "']")
                                present_current_row = $(
                                    '<tr parent_product_id="' + lot_rec[lot].parent_product_id +
                                    '" parent_lot_id="' + lot_rec[lot].parent_lot_id +
                                    '" data-row-lot-id="'+ lot_rec[lot].lot_id +
                                    '"><td><span class="o_stock_reports_foldable o_stock_reports_caret_icon" level="' + lot_rec[lot].level +
                                    '" style="margin-left:' + current_level_margin +
                                    'px"><i class="fa fa-fw fa-caret-down custom_fold_unfold"></i>' +
                                    '<a action="open_lot_record" href="#" data-lot-id="'+ lot_rec[lot].lot_id +
                                    '" data-non-lot-id="'+ lot_rec[lot].non_lot_id + '">' + lot_rec[lot].lot_number +
                                    '</a></span><input type="hidden" class="from-control lot_id" data-id="' + lot_rec[lot].parent_lot_id +
                                    '"></input></td><td class="o_report_line_header"><span>' + lot_rec[lot].internal_reference +
                                    '</span></td><td class="o_report_line_header"><span>' + lot_rec[lot].product +
                                    '</span></td><td class="o_report_line_header product_id"><span>' + lot_rec[lot].product_id +
                                    '</span></td><td class="o_report_line_header"><span>' + lot_rec[lot].lot_version +
                                    '</span></td><td class="o_report_line_header"><span class="report_plus_button">' +
                                    '<i class="add_button">Add</i></span><span class="report_edit_button">' +
                                    '<i class="edit_button">Edit</i></span><span class="report_minus_button">' +
                                    '<i class="delete_button">Delete</i></span></td></tr>'
                                ).insertAfter(present_current_row)
                            } else {
                                var present_current_row = $(
                                    '<tr parent_product_id="' + lot_rec[lot].parent_product_id +
                                    '" parent_lot_id="' + lot_rec[lot].parent_lot_id +
                                    '" data-row-lot-id="'+ lot_rec[lot].lot_id +
                                    '"><td><span class="o_stock_reports_foldable o_stock_reports_caret_icon" level="' + lot_rec[lot].level +
                                    '" style="margin-left:' + current_level_margin +
                                    'px"><i class="fa fa-fw fa-caret-down custom_fold_unfold"></i>' +
                                    '<a action="open_lot_record" href="#" data-lot-id="'+ lot_rec[lot].lot_id +
                                    '" data-non-lot-id="'+ lot_rec[lot].non_lot_id + '">' + lot_rec[lot].lot_number +
                                    '</a></span><input type="hidden" class="from-control lot_id" data-id="' + lot_rec[lot].parent_lot_id +
                                    '"></input></td><td class="o_report_line_header"><span>' + lot_rec[lot].internal_reference +
                                    '</span></td><td class="o_report_line_header"><span>' + lot_rec[lot].product +
                                    '</span></td><td class="o_report_line_header product_id"><span>' + lot_rec[lot].product_id +
                                    '</span></td><td class="o_report_line_header"><span>' + lot_rec[lot].lot_version +
                                    '</span></td><td class="o_report_line_header"><span class="report_plus_button">' +
                                    '<i class="add_button">Add</i></span><span class="report_edit_button"><i class="edit_button">Edit</i></span><span class="report_minus_button"><i class="delete_button">Delete</i></span></td></tr>'
                                ).insertAfter(current_row)
                            }
                            if (lot_rec[lot].is_as_maintained_user == false) {
                                //if current user have not access for as-maintained structure configuration
                                $('.as_maintained_table tbody').find('span.report_plus_button').hide()
                                $('.as_maintained_table tbody').find('span.report_edit_button').hide()
                                $('.as_maintained_table tbody').find('span.report_minus_button').hide()
                            }
                            if (lot_rec[lot].is_non_traceable == true) {
                                //if there is non-traceable lot, then hide add button
                                present_current_row.find('span.report_plus_button').hide()
                            }
                        }
                    }
                    $CurretElement.attr('class', 'o_stock_reports_foldable o_stock_reports_caret_icon')
                    $CurretElement.css({marginLeft: previous_level_margin + "px"})
                }
                else {
                    var previous_level_margin = parseInt($CurretElement.css('marginLeft').replace(/[a-z]/gi, ''))
                    $CurretElement.attr('class', 'o_stock_reports_foldable o_stock_reports_caret_icon')
                    $CurretElement.css({marginLeft: previous_level_margin + "px"})
                }
            }
            else {
                Dialog.alert(self, _t("There is no installed location for this lot."), {
                    title: _t('Note'),
                });
            }
        });
    },

    collapse: function(e) {
        var self = this;
        var $CurretElement = $('.as_maintained_table tbody').find('span.o_stock_reports_foldable')
        var current_row = $('.as_maintained_table tbody').find("tr")[0]
        $($('.as_maintained_table tbody')[0]).find('i.custom_fold_unfold').replaceWith("<i class='fa fa-fw fa-caret-right custom_fold_unfold'></i>");
        var all_row_except_current_row = $(current_row).nextAll('tr')
        $('#expand_button').show()
        $('#button_collapse').hide()
        for (var i = 0; i < all_row_except_current_row.length; i++) {
            $(all_row_except_current_row[i]).remove()
        }
        $CurretElement.attr('class', 'o_stock_reports_unfoldable o_stock_reports_caret_icon')
    },

    open_lot_record: function(e){
        var self = this;
        var lot_id = $(e.target).data('lot-id');
        var non_lot_id = $(e.target).data('non-lot-id');
        if (lot_id != 'undefined'){
            self.do_action({
                name: 'Lots/Serial Numbers',
                res_model: 'stock.production.lot',
                views: [[false, 'form']],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: lot_id,
                target: 'current'
            });
        }
        else if(non_lot_id != 'undefined'){
            self.do_action({
                name: 'Non-Traceable Entries',
                res_model: 'stock.production.quant',
                views: [[false, 'form']],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: non_lot_id,
                target: 'current'
            });
        }
    },

});

core.action_registry.add('as_maintained_report_generic', AsMaintainedReport);
return AsMaintainedReport;
});
