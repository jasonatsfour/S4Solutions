
odoo.define('zip_product', function (require) {
    "use strict";

    var basic_fields = require('web.basic_fields');

    basic_fields.UrlWidget.include({
        /**
         * @override
         */
        init: function () {
            this._super.apply(this, arguments);
        },

        /**
         * In readonly, the widget needs to be a link with proper href and proper
         * support for the design, which is achieved by the added classes. We
         * will also introduce the server URL if defined as well
         *
         * @override
         * @private
         */
        _renderReadonly: function () {
            // check to see if we are prefixing the value with either
            // the aras url (Aras Item) or the Aras Asset URL
            var aras_field = this.attrs.aras_url|| this.attrs.options.aras_url;
            var asset_field = this.attrs.asset_url || this.attrs.options.asset_url;
            if (aras_field && !asset_field) {
                var field_value = this.recordData[aras_field];
                if (_.isObject(field_value) && _.has(field_value.data)) {
                    field_value = field_value.data.display_name;
                }
            } else if (!aras_field && asset_field) {
                var field_value = this.recordData[asset_field];
                if (_.isObject(field_value) && _.has(field_value.data)) {
                    field_value = field_value.data.display_name;
                }              
            }
            
            var prefix = this.value;
            if (field_value) {
                prefix = field_value + this.value;
            }

            console.log("Updating the widget href ("+this.value+") to " + prefix);
            this.$el.text(this.attrs.text || this.value)
                .addClass('o_form_uri o_text_overflow')
                .attr('target', '_blank')
                .attr('href', prefix);
        },
    });

});