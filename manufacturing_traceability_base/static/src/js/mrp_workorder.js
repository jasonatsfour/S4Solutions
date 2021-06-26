odoo.define('manufacturing_traceability_base.mrp_workorder', function (require) {
    "use strict";

    var basic_fields = require('web.basic_fields');
    var workorder_tablet = require('mrp_workorder.update_kanban');
    var view_registry = require('web.view_registry');
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');

    var TabletListView = workorder_tablet.TabletListView;

    function tabletRenderButtons($node) {
        var self = this;
        this.$buttons = $('<div/>');
        this.$buttons.html('<button class="btn btn-secondary back-button"><i '+
        'class="fa fa-arrow-left"/></button>');
        this.$buttons.find('.back-button').on('click', function () {
            self.do_action('mrp.mrp_workcenter_kanban_action', {clear_breadcrumbs: true});
        });
        if (self.initialState.context && self.initialState.context.need_to_create_wo &&
        self.initialState.context.operation_edit_allowed && self.initialState.context.is_manufacturing_admin){
            $('<button class="btn btn-primary create_wo" accesskey="c">Create</button> '+
            '<button class="btn btn-primary append_wo" accesskey="a">Append</button>').appendTo(self
            .$buttons);
            var active_id = self.initialState.context ? self.initialState.context.active_id : false
            // Create wo based on creating operation
            this.$buttons.find('.create_wo').on('click', function () {
                self.do_action({
                    name: 'Operations',
                    type: 'ir.actions.act_window',
                    res_model: 'mrp.routing.workcenter',
                    target: 'current',
                    views: [[false, "form"]],
                    context: {'need_to_create_wo': true, 'production_id': active_id,
                    'operation_edit_allowed': self.initialState.context.operation_edit_allowed,
                    'default_company_id': self.getSession().company_id,
                    'is_manufacturing_admin': self.initialState.context.is_manufacturing_admin},
                });
            });

            // Select Route to create wo
            this.$buttons.find('.append_wo').on('click', function () {
                self.do_action({
                    name: 'Routing',
                    type: 'ir.actions.act_window',
                    res_model: 'mrp.routing',
                    target: 'new',
                    views: [[false, "list"]],
                    context: {'need_to_create_wo': true, 'production_id': active_id, 'no_create_edit': true,
                    'operation_edit_allowed': self.initialState.context.operation_edit_allowed,
                    'is_manufacturing_admin': self.initialState.context.is_manufacturing_admin},
                }, {clear_breadcrumbs: true});
            });
        }
        this.$buttons.appendTo($node);
    }

    var TabletListController = ListController.extend({
        renderButtons: function ($node) {
            return tabletRenderButtons.apply(this, arguments);
        },
    });

    var TabletListView = TabletListView.include({
        config: _.extend({}, ListView.prototype.config, {
            Controller: TabletListController,
        }),
    });

});