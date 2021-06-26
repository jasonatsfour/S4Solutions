odoo.define('clear_to_build.mrp_bom_report', function (require) {
'use strict';

var core = require('web.core');
var framework = require('web.framework');

var QWeb = core.qweb;
var _t = core._t;
var MrpBomReport = require('mrp.mrp_bom_report');

MrpBomReport.include({

    get_bom: function(event) {
      var self = this;
      var $parent = $(event.currentTarget).closest('tr');
      var activeID = $parent.data('id');
      var productID = $parent.data('product_id');
      var lineID = $parent.data('line');
      var qty = $parent.data('qty');
      var level = $parent.data('level') || 0;
      self.given_context.Warehouse = document.getElementById("o_mrp_bom_report_warehouse").value || 0;
      return this._rpc({
              model: 'report.mrp.report_bom_structure',
              method: 'get_bom',
              args: [
                  activeID,
                  productID,
                  parseFloat(qty),
                  lineID,
                  level + 1,
              ],
              context: this.given_context,
          })
          .then(function (result) {
              self.render_html(event, $parent, result);
          });
    },
    _reload_report_type: function () {
        this.$('.o_mrp_bom_cost.o_hidden, .o_mrp_prod_cost.o_hidden, .o_mrp_on_hand.o_hidden, .o_mrp_bom_report_warehouse.o_hidden').toggleClass('o_hidden');
        if (this.given_context.report_type === 'all') {
            this.$('.o_mrp_on_hand').toggleClass('o_hidden');
            this.$('.o_mrp_bom_report_warehouse').toggleClass('o_hidden');
        }
        if (this.given_context.report_type === 'bom_structure') {
           this.$('.o_mrp_bom_cost, .o_mrp_prod_cost, .o_mrp_on_hand, .o_mrp_bom_report_warehouse').toggleClass('o_hidden');
        }
        if (this.given_context.report_type === 'clear_to_build') {
           this.$('.o_mrp_bom_cost, .o_mrp_prod_cost').toggleClass('o_hidden');
        }
    },
    renderSearch: function () {
        this.$buttonPrint = $(QWeb.render('mrp.button'));
        this.$buttonPrint.find('.o_mrp_bom_print').on('click', this._onClickPrint.bind(this));
        this.$buttonPrint.find('.o_mrp_bom_print_unfolded').on('click', this._onClickPrint.bind(this));
        this.$searchView = $(QWeb.render('mrp.report_bom_search', _.omit(this.data, 'lines')));
        this.$searchView.find('.o_mrp_bom_report_qty').on('change', this._onChangeQty.bind(this));
        this.$searchView.find('.o_mrp_bom_report_variants').on('change', this._onChangeVariants.bind(this));
        this.$searchView.find('.o_mrp_bom_report_type').on('change', this._onChangeType.bind(this));
        this.$searchView.find('.o_mrp_bom_report_warehouse').on('change', this._onChangeWarehouse.bind(this));
    },
    _onChangeWarehouse: function (ev) {
        this.given_context.Warehouse = $(ev.currentTarget).val();
        this._reload();
    },
});


});
