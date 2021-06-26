odoo.define('manufacturing_traceability_base.list_controllers', function (require) {
    "use strict";

    var core = require('web.core');
    var rpc = require('web.rpc');
    var BasicController = require('web.BasicController');
    var ListController = require('web.ListController');

    ListController.include({

        init: function (parent, model, renderer, params) {
            this._super.apply(this, arguments);
            this.append_wo_button = false;
            this.production_id = this.initialState.context ? parseInt(this.initialState.context.production_id) : false
            this.need_to_create_wo = this.initialState.context ? this.initialState.context.need_to_create_wo: false
            this.order_handling_enabled = this.initialState.context ? this.initialState.context.operation_edit_allowed : false
            this.is_manufacturing_admin = this.initialState.context ? this.initialState.context.is_manufacturing_admin : false
            if (this.initialState.context && this.initialState.context.no_create_edit){
                this.activeActions['create'] = false
                this.activeActions['edit'] = false
                this.activeActions['export_xlsx'] = false
                this.activeActions['duplicate'] = false
                this.activeActions['delete'] = false
            }
        },
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            this.append_wo_button = this.$buttons && this.order_handling_enabled ? this.$buttons.find(
            '.o_button_create_wo_based_on_selected_operation') : false
            if (this.append_wo_button){
                this.append_wo_button.on("click", this.createWOs.bind(this));
                this.append_wo_button.hide();
            }
        },

        _onSelectionChanged: function (ev) {
            this._super.apply(this, arguments);
            if (this.append_wo_button){
                if (this.selectedRecords.length > 0 && this.production_id){this.append_wo_button.show()}else{this.append_wo_button
                .hide()}
            }
        },

        createWOs: function(ev){
            var self = this;
            return self._rpc({
                model: "mrp.production",
                method: "create_workorder_for_given_operation",
                args: [self.production_id, self.getSelectedIds(), true],
            })
            .then(function (result) {
                result[1]['context'] = {'operation_edit_allowed': self.order_handling_enabled,
                 'need_to_create_wo': self.need_to_create_wo,
                 'is_manufacturing_admin': self.is_manufacturing_admin}
                self.do_action(result[1], {clear_breadcrumbs: false});
            });
        },
    });
});