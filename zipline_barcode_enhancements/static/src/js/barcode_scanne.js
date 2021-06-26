odoo.define('zipline_barcode_enhancements.barcode_scanne', function (require) {
"use strict";

var ClientAction = require('stock_barcode.ClientAction');

function isChildOf(locationParent, locationChild) {
    return _.str.startsWith(locationChild.parent_path, locationParent.parent_path);
}
var core = require('web.core');
var _t = core._t;


ClientAction.include({

    /**
     * Handle what needs to be done when a source location is scanned.
     *
     * @param {string} barcode scanned barcode
     * @param {Object} linesActions
     * @returns {Promise}
     */
    _step_source: function (barcode, linesActions) {
        var self = this;
        this.currentStep = 'source';
        var errorMessage;

        /* Bypass this step in the following cases:
           - the picking is a receipt
           - the multi location group isn't active
        */
        var sourceLocation = this.locationsByBarcode[barcode];
        if (sourceLocation  && ! (this.mode === 'receipt' || this.mode === 'no_multi_locations')) {
            var SorLocation = this._getLocationId();
            if (this.CurrentStockLocation.is_update == 1) {
                SorLocation = this.CurrentStockLocation
            }
            const locationId = SorLocation;
            if (locationId && !isChildOf(locationId, sourceLocation)) {
                errorMessage = _t('This location is not a child of the main location.');
                return Promise.reject(errorMessage);
            } else {
                // There's nothing to do on the state here, just mark `this.scanned_location`.
                linesActions.push([this.linesWidget.highlightLocation, [true]]);
                if (this.actionParams.model === 'stock.picking') {
                    linesActions.push([this.linesWidget.highlightDestinationLocation, [false]]);
                }
                this.scanned_location = sourceLocation;
                this.currentStep = 'product';
                return Promise.resolve({linesActions: linesActions});
            }
        }
        /* Implicitely set the location source in the following cases:
            - the user explicitely scans a product
            - the user explicitely scans a lot
            - the user explicitely scans a package
        */
        // We already set the scanned_location even if we're not sure the
        // following steps will succeed. They need scanned_location to work.
        this.scanned_location = {
            id: this.pages ? this.pages[this.currentPageIndex].location_id : this.currentState.location_id.id,
            display_name: this.pages ? this.pages[this.currentPageIndex].location_name : this.currentState.location_id.display_name,
        };
        linesActions.push([this.linesWidget.highlightLocation, [true]]);
        if (this.actionParams.model === 'stock.picking') {
            linesActions.push([this.linesWidget.highlightDestinationLocation, [false]]);
        }

        return this._step_product(barcode, linesActions).then(function (res) {
            return Promise.resolve({linesActions: res.linesActions});
        }, function (specializedErrorMessage) {
            delete self.scanned_location;
            self.currentStep = 'source';
            if (specializedErrorMessage){
                return Promise.reject(specializedErrorMessage);
            }
            var errorMessage = _t('You are expected to scan a source location.');
            return Promise.reject(errorMessage);
        });
    },

    _onBarcodeScanned: function (barcode) {
        var self = this;
        return this.stepsByName[this.currentStep || 'source'](barcode, []).then(function (res) {
            /* We check now if we need to change page. If we need to, we'll call `this.save` with the
             * `new_location_id``and `new_location_dest_id` params so `this.currentPage` will
             * automatically be on the new page. We need to change page when we scan a source or a
             * destination location ; if the source or destination is different than the current
             * page's one.
             */
            var prom = Promise.resolve();
            var currentPage = self.pages[self.currentPageIndex];
            if (
                (self.scanned_location &&
                 ! self.scannedLines.length &&
                 self.scanned_location.id !== currentPage.location_id
                ) ||
                (self.scanned_location_dest &&
                 self.scannedLines.length &&
                 self.scanned_location_dest.id !== currentPage.location_dest_id
                )
            ) {
                // The expected locations are the scanned locations or the default picking locations.
                var expectedLocationId = self.scanned_location.id;
                var expectedLocationDestId;
                if (self.actionParams.model === 'stock.picking'){
                    expectedLocationDestId = self.scanned_location_dest &&
                                             self.scanned_location_dest.id ||
                                             self.currentState.location_dest_id.id;
                }

                if (expectedLocationId !== currentPage.location_id ||
                    expectedLocationDestId !== currentPage.location_dest_id
                ) {
                    var params = {
                        new_location_id: expectedLocationId,
                    };
                    if (expectedLocationDestId) {
                        params.new_location_dest_id = expectedLocationDestId;
                    }
                    var is_scanned = 1;
                    if (self.CurrentStockLocation.is_update == 1) {
                        is_scanned = 0;
                    }
                    if (is_scanned === 1) {
                        prom = self._save(params).then(function () {
                            return self._reloadLineWidget(self.currentPageIndex);
                        });
                    } else {
                        document.getElementsByClassName('o_barcode_summary_location_src')[0].textContent= self.CurrentStockLocation.display_name;
                    }
                }
            }

            // Apply now the needed actions on the different widgets.
            if (self.scannedLines && self.scanned_location_dest) {
                self._endBarcodeFlow();
            }
            var linesActions = res.linesActions;
            var always = function () {
                _.each(linesActions, function (action) {
                    action[0].apply(self.linesWidget, action[1]);
                });
            };
            prom.then(always).guardedCatch(always);
            return prom;
        }, function (errorMessage) {
            self.do_warn(_t('Warning'), errorMessage);
        });
    },

    _onBarcodeScannedHandler: function (barcode) {
        var self = this;
        this._rpc({
            'model': 'stock.picking',
            'method': 'get_update_source_location',
            'args': ['',self.context.active_ids, barcode],
        }).then(function (res) {
            self.CurrentStockLocation = res;
        });

        this._rpc({
            model: 'stock.picking',
            method: 'update_stock_scanned',
            args: [self.context.active_ids],
        });

        this.mutex.exec(function () {
            setTimeout(function() {
                if (self.mode === 'done' || self.mode === 'cancel') {
                    self.do_warn(_t('Warning'), _t('Scanning is disabled in this state.'));
                    return Promise.resolve();
                }
                console.log("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&", self.CurrentStockLocation.barcode);
                console.log("JJJJJJJJJJJJJJJJJJJJJJJJ", self.context.active_ids);
                var commandeHandler = self.commands[self.CurrentStockLocation.barcode];
                if (commandeHandler) {
                    return commandeHandler();
                }
                return self._onBarcodeScanned(barcode).then(function () {
                    console.log("::::::::::::::::::::::", this);
//                    var recordId = this.actionParams.pickingId

                    // FIXME sle: not the right place to do that
                    if (self.show_entire_packs && self.lastScannedPackage) {
                        return self._reloadLineWidget(self.currentPageIndex);
                    }
                });
            }, 1000);

        });
    },

//	_onBarcodeScannedHandler: function(barcode){
//		this._super.apply(this, arguments)
//		var recordId = this.actionParams.pickingId
//		var self = this;
//        var def = this._rpc({
//                model: 'stock.picking',
//                method: 'update_stock_scanned',
//                args: [recordId],
//            }).then(function (res) {});
//		}
	});


});