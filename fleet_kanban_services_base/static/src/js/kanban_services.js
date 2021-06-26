odoo.define('fleet_kanban_services_base.fleet_services_kanban', function (require) {
"use strict";

var Widget = require('web.Widget');
var core = require('web.core');
var AbstractAction = require('web.AbstractAction');
var Dialog = require('web.Dialog');
var ajax = require('web.ajax');
var _t = core._t;

window.data = '';
window.test_index = 0;

var FleetServicesKanban = AbstractAction.extend({
    contentTemplate: 'fleet_services_kanban_template',

    events: {
        "click .o_barcode_fleet_services_scan": function () { this.scan_barcode() },
        "click #discrepancy_confirm_button":function() { this.confirm_discrepancy() },
        "click #cancel_scan": function() { this.cancel_scan() },
        "click #vehicle_services_record": function () { this.open_vehicle_services_record() },
        'change .custom-file-input': 'upload_image',
        'click .o_select_file_button': function () { this.$('.custom-file-input').click();},
        'click [action]': 'open_vehicle_discrepancy_record',
        "click #open_repair_order" : function() { this.open_repair_order() },
        "click #new_discrepancy_record": function () { this.scan_barcode() },
        "click #open_all_service_request": function () { this.open_all_service_request() },
        "click #repair_order_list": function () { this.repair_order_list() },
        "click #attachment_del": function () {this.attachment_del()},
    },

    start: function() {
        var self = this;
        this._super;
        if (this.$el != null){
            this.$el.find('.o_barcode_fleet_services_scan').focus()
            this.$el.find("#barcode_unmatched").hide()
            this.$el.find("#barcode_matched").hide()
            this.$el.find("#discrepancy_created").hide()
        }
    },

    repair_order_list: function (ev) {
        var self = this;
        var vehicle_services = $("#vehicle_services_record").val();
            self._rpc({
                model: 'fleet.repair',
                method: 'get_repair_order_rec',
                args: [vehicle_services],
            }).then(function (data) {
            if (data != false){
                var vehicle_service_rec;
                var repair_order = JSON.stringify(data);
                if ($('#repair_order_rec').length == 1) {
                    $('#repair_order_rec').remove()
                }
                if ($('#vehicle_service_add').length == 1) {
                    $('#vehicle_service_add').remove()
                }
                var target_parent_div = $('#repair_order').find(".form-group");
                target_parent_div.find(".form-control-warning").addClass('remove');
                for (var i = 0; i < data.length; i++) {
                    if (i == 0) {
                        vehicle_service_rec = data[i].vehicle_services
                    }
                    $('#mytable').append(_t("<tr><td><input type='radio'name='repair_order' class='form-check'/>" + data[i]['reference'] +"</td><td class='text-center><input type='hidden name='vehicle_service' class='from-control' t-att-value=" + data[i]['vehicle_services'] + "/> <td class='text-center'>" + data[i]['vehicle_brand'] +"</td><td class='text-center'>" + data[i]['vehicle_model'] +"</td><td>"+ data[i]['responsible'] +"</td></tr>"))
                }
            }
            if (data == false){
                self.dialog.close()
                Dialog.alert(self, _t("There is no repair order exist for this type of service request."), {
                    title: _t('No repair order exist'),
                });
            }
        });

        var $content = $('<div>').append(_t("<table class='table table-condensed' id='mytable'> <tr><th>Reference</th><th class='text-center'>Vehicle Brand</th><th class='text-center'>Vehicle Model</th><th>Responsible</th></tr><tbody id='repair_order_rec'></tbody></table> <small class='text-danger form-control-warning'>Please select an Product</small>"));
        self.dialog = new Dialog(self, {
            title: _t('Select repair order to add service request.'),
            buttons: [{text: _t('ADD'), classes: 'btn-primary',id:'vehicle_service_add', close: true,click: function () {
                    self.repair_order_data();

                }}, {text: _t('CANCEL'), close: true}],
            $content: $content,
        });
        self.dialog.open()
    },

    repair_order_data : function(){
        var self = this;
        var vehicle_services = $("#vehicle_services_record").val();
        var cols = []
        var target_parent_div = $('#repair_order').closest(".form-group");
        if ($(".table").find("input[type=radio]:checked").length != 1){
            target_parent_div.find(".form-control-warning").show();
        }
        else if ($(".table input[type=radio]:checked").length == 1){
            $(".table input[type=radio]:checked").each(function () {
                var row = $(this).closest("tr")[0];
                for (var i = 0; i < row.cells.length; i++) {
                    cols.push({[i]:$.trim(row.cells[i].textContent)})
                }
            });
            var fleet_repair_details = JSON.stringify(cols);
            self._rpc({
                model: 'fleet.repair',
                method: 'add_vehicle_service',
                args: [fleet_repair_details,parseInt(vehicle_services)],
            }).then(function () {
                // dialog.$el.modal('hide');
            })
        }
    },

    attachment_del: function(){
        if (confirm("Delete Attachments?")) {
            $(".gallery input[type=checkbox]:checked").each(function () {
               var id = $(this).attr('id')
               var img_name = document.getElementById(id)
               $(this).next('img').remove()
               $(this).prev('.image_name').remove()
               $(this).remove()
            });
        }
    },
    
    upload_image : function(){
        var self = this;
        var img = $('.custom-file-input')
        var values_list = [];
        var values = {}
        for (var i = 0, len = img[0].files.length; i < len; i++) {
            var file = img[0].files[i]
            var filereader = new FileReader();
            var rt = [];
            filereader.readAsDataURL(file);
            var name = file.name
            // Store Image Name here so that we can fetch while creating Vehicle Descrepancy.
            $(".gallery").append('<input type="hidden" class="image_name" id="image_name_'+window.test_index+'" value="'+ name + '"/>')
            if (!$("#image_name_"+i).val()) {
                $("#image_name_"+i).remove()
            }
            window.test_index += 1; 
            var count = -1
            filereader.onload = function (file) {
                var data = file.target.result;
                count += 1;
                // Append Source here to create attachment
                $(".gallery").append( '<input type="checkbox" name="del_img" class="form-check" id="image_checkbox" style="vertical-align: top;position:absolute;"/><img class="mb-32 vehicle_img" id="upload_img" itemprop="image" style="width: 92px; height: 92px;margin:10px;" src="'+ data+ '" />');
                var data64 = data.split(',')[1];
            };
        }
        return values_list
    },

    scan_barcode: function(barcode_data) {
        var self = this;
        var barcode_data = $('#barcode').val();
        this._rpc({
            model: 'fleet.vehicle',
            method: 'match_barcode',
            args: [barcode_data],
            context: self.context
        }).then(function (data){
            $('#barcode').on('input', function(){
                    $("#barcode_unmatched").hide();
                });
            //Raise warning if Data not matched.
            if (data == false){
                $("#barcode_unmatched").show();
                $("#barcode_matched").hide();
            }
            else if (data){
                // if data get then it will redirected to vehicle discrepancy.
                $('.o_fleet_services_kiosk_mode').hide();
                $("#barcode_unmatched").hide();
                $("#barcode_matched").show();
                $("#discrepancy_created").hide();
                $(".barcode_field").val('');
                $("#title").val('');
                $("#availability").val('');
                $("#observed_date").val('');
                $("#description").val('');
                $("#x_flight_hours").val(data.x_flight_hours);
                $("#x_hw_config").val(data.x_hw_config);
                var img = $('.custom-file-input')
                for (var i = 0; i < img[0].files.length; i++) {
                    $("#upload_img").remove();
                    $("#image_name_"+i).val('')
                }
                $(".custom-file-input").val('');
                // $("#image_name_"+0).remove();
                $("#priority").val('');
                $("#vehicle_id").val(data.vehicle_id);
                $("#x_serial_no").val(data.x_serial_no);
                $("#vehicle_number").val(data.fleet_vehicle_number);
                $("#x_location").val(data.x_location);
                $("#x_location_id").val(data.x_location_id);
                $("#x_availability").val(data.vehicle_status_rec);

                // To remove option tag when we again create the services as per discrepancy created.
                if ($("#discrepancy_type").find("option")) {
                    $("#discrepancy_type").find("option").remove();
                }
                //The very first option of many2one(i.e discrepancy_type) field as none
                $("#discrepancy_type").append( '<option value="' + '">' + '</option>');
                for (var i = 0; i < data.vehicle_discrepancy_type_rec.length; i++) {
                    $("#discrepancy_type").append( '<option value="' + data.vehicle_discrepancy_type_rec[i] + '">' + data.vehicle_discrepancy_type_rec[i] + '</option>');
                }

                if ($("#observed_during").find("option")) {
                    $("#observed_during").find("option").remove();
                }
                $("#observed_during").append( '<option value="' + '">' + '</option>');
                for (var i = 0; i < data.vehicle_observed_during_rec.length; i++) {
                    $("#observed_during").append( '<option value="' + data.vehicle_observed_during_rec[i] + '">' + data.vehicle_observed_during_rec[i] + '</option>');
                }

                if ($("#hw_failure_mode").find('option:selected').length != 0) {
                    $('#hw_failure_mode').multiselect('destroy');
                    $('#hw_failure_mode').multiselect({
                        includeSelectAllOption: true
                    });
                }
                else {
                    for (var i = 0; i < data.vehicle_hw_failure_mode_rec.length; i++) {
                        $("#hw_failure_mode").append( '<option value="' + data.vehicle_hw_failure_mode_rec[i] + '">' + data.vehicle_hw_failure_mode_rec[i] + '</option>');
                    }
                    $('#hw_failure_mode').multiselect({
                        includeSelectAllOption: true
                    });
                 }

                var now = new Date();
                $("#observed_date").val(new Date(now.getTime()-now.getTimezoneOffset()*60000).toISOString().substring(0,19));
            }
        });
    },


    confirm_discrepancy : function(){
        var self = this;
        if ($("#priority").val() == 'critical' && ($('#is_grounded').val() != '1' || $('#is_grounded').val() == '')) {
            var $content = $('<div>').append(_t("Choosing 'critical' priority will ground this Vehicle. Do you wish to proceed ? Or change the priority."));
            this.dialog = new Dialog(this, {
                title: _t('Alert'),
                buttons: [{text: _t('YES'), classes: 'btn-primary', close: true,click: function () {
                        $('#is_grounded').val('1')
                        self.check_display_data();
                    }}, {text: _t('CANCEL'), close: true}],
                $content: $content,
            });
            this.dialog.open();
        }
        else
        $('#is_grounded').val('0')
        self.check_display_data();
         
    },

    check_display_data : function(){
        var self = this;
        if ( ($("#priority").val() == 'critical' && $('#is_grounded').val() == '1') || $("#priority").val() != 'critical') {
        var data64 = ''
        var vehicle_images = [];
        var img_values = {};
        var vehicle_id = parseInt($("#vehicle_id").val());
        var x_serial_no = $("#x_serial_no").val();
        var vehicle_number = $("#vehicle_number").val();
        var title = $("#title").val();
        var observed_date = $("#observed_date").val();
        var x_location = $("#x_location").val();
        var x_location_id = $("#x_location_id").val();
        var availability = $("#x_availability").val();
        var x_flight_hours = $("#x_flight_hours").val();
        var x_hw_config = $("#x_hw_config").val();
        var priority = $("#priority").val();
        var discrepancy_type = $("#discrepancy_type").val();
        var observed_during = $("#observed_during").val();
        var hw_failure_mode = $("#hw_failure_mode").val();
        var description = $("#description").val();
        // Get Multiple Images and it's name
        $( ".vehicle_img" ).each(function( index ) {
            var data64 = $(this)[0].currentSrc.split(',')[1];
            var data = $(this)[0].currentSrc
            img_values['type'] = 'binary'
            var file_name = $(this).prev().prev().val()
            vehicle_images.push({'data': data64,'name': file_name})
        });
        if(!title) {
            $("#title").addClass("rq-border").after('Please select the title.')
            return false;
        }
        else {
            $("#title").removeClass("rq-border")
            if ($("#title").get(0).nextSibling) {
                $("#title").get(0).nextSibling.remove();
            }
        }

        if(!observed_during) {
            $("#observed_during").addClass("rq-border").after('Please select the Observed during.')
            return false;
        }
        else {
            $("#observed_during").removeClass("rq-border")
            if ($("#observed_during").get(0).nextSibling) {
                $("#observed_during").get(0).nextSibling.remove();
            }
        }

        if ($("#hw_failure_mode").val()[0])
        {
            $("#hw_failure_mode").removeClass("rq-border")
            if ($("#hw_failure_mode").get(0).nextSibling) {
                $("#hw_failure_mode").get(0).nextSibling.remove();
            }
        }
        else
        {
             $("#hw_failure_mode").addClass("rq-border").after('Please select as least one HW Failure Mode.')
            return false;
        }

        if(!observed_date) {
            $("#observed_date").addClass("rq-border").after('Please select the observed datetime.')
            return false;
        }
        else {
            $("#observed_date").removeClass("rq-border")
            if ($("#observed_date").get(0).nextSibling) {
                $("#observed_date").get(0).nextSibling.remove();
            }
        }

        if(!priority) {
            $("#priority").addClass("rq-border").after('Please select the priority.')
            return false;
        }
        else {
            $("#priority").removeClass("rq-border")
            if ($("#priority").get(0).nextSibling) {
                $("#priority").get(0).nextSibling.remove();
            }
        }

        var vehicle_discrepancy_dict = {
            'vehicle_id': vehicle_id,
            'x_serial_no': x_serial_no,
            'vehicle_number': vehicle_number,
            'title': title,
            'observed_date': observed_date,
            'x_location': x_location,
            'x_location_id': x_location_id,
            'x_availability': availability,
            'x_flight_hours': x_flight_hours,
            'x_hw_config': x_hw_config,
            'priority': priority,
            'discrepancy_type': discrepancy_type,
            'observed_during': observed_during,
            'hw_failure_mode': hw_failure_mode,
            'description': description,
            'attachment_ids':vehicle_images ,
        }
        window.test_index = 0;
        this._rpc({
                model: 'fleet.vehicle',
                method: 'confirm_vehicle_discrepancy',
                args: [[vehicle_discrepancy_dict]],
                context: self.context
            }).then(function (match_data) {
                if (match_data){
                    $('.o_fleet_services_kiosk_mode').hide();
                    $("#barcode_unmatched").hide();
                    $("#barcode_matched").hide();
                    $("#discrepancy_created").show();
                    $(".barcode_field").val('').focus();
                    $("#vehicle_discrepancy_record").val(match_data.vehicle_discrepancy_id)

                    // To remove span tag when discrepancy is again created
                    if ($("#vehicle_discrepancy_record").find("span")) {
                        $("#vehicle_discrepancy_record").find("span").remove();
                    }
                    $("#vehicle_discrepancy_record").append('<span> Discrepancy <bold>#<a action="open_vehicle_discrepancy_record" href="#" data-id=' + match_data.vehicle_discrepancy_id + '>' + match_data.vehicle_discrepancy_name + '</a></bold> has been created successfully for Vehicle. </span>');
                    $("#vehicle_services_record").val(match_data.vehicle_services_id)

                    // To remove span tag when service request is again created
                    //by newly creation of discrepancy
                    if ($("#vehicle_services_record").find("span")) {
                        $("#vehicle_services_record").find("span").remove();
                    }
                    $("#vehicle_services_record").append('<span> Service Request <bold>#<a action="open_vehicle_services_record" href="#" data-id=' + match_data.vehicle_services_id + '>' + match_data.vehicle_services_name + '</a></bold> has been created successfully based on this Discrepancy. </span>');

                    // To remove span tag in open_repair_order when discrepancy is again created
                    if ($("#open_repair_order").find("span")) {
                        $("#open_repair_order").find("span").remove();
                    }
                    $("#open_repair_order").append('<span><bold><a action="open_repair_order"> Create Repair order </a></bold> for Service Request <bold>#' + match_data.vehicle_services_name + '</span>');
                    $('#barcode').val(match_data.discrepancy_barcode)
                    $('#is_grounded').val('')
                    $("#priority").val('')

                    if ($("#title").get(0).nextSibling) {
                        $("#title").get(0).nextSibling.remove();
                    }
                    if ($("#priority").get(0).nextSibling) {
                        $("#priority").get(0).nextSibling.remove();
                    }
                }
            })
        }
        $( "#cancel_scan" ).click(function() {
            location.reload(true);
        });
    },

    open_vehicle_discrepancy_record : function() {
        var self = this;
        if ($("#vehicle_discrepancy_record").val()) {
            self.do_action({
                name: 'Vehicle Discrepancy',
                res_model: 'vehicle.discrepancy',
                views: [[false, 'form']],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: parseInt($("#vehicle_discrepancy_record").val()),
                target: 'current'
            });
        }
    },

    open_vehicle_services_record : function(){
        var self = this;
        if ($("#vehicle_services_record").val()){
            self.do_action({
                name: 'Vehicle Services',
                res_model: 'vehicle.services',
                views: [[false, 'form']],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: parseInt($("#vehicle_services_record").val()),
                target: 'current'
            });
        }
    },

    open_repair_order: function(){
        var self = this;
        var vehicle_service_id = parseInt($("#vehicle_services_record").val())
        self.do_action({
            name: 'Fleet Repair',
            res_model: 'fleet.repair',
            views: [[false, 'form']],
            type: 'ir.actions.act_window',
            view_type: 'form',
            view_mode: 'form',
            target: 'current',
            context: {
                    'default_vehicle_id': parseInt($("#vehicle_id").val()),
                    'vehicle_services_id': vehicle_service_id,
                }
        });
    },

    open_all_service_request: function(){
        var self = this;
        self.do_action({
                name: 'Vehicle Services',
                res_model: 'vehicle.services',
                views: [[false, 'list'], [false, 'form']],
                type: 'ir.actions.act_window',
                view_type: 'tree',
                view_mode: 'tree',
                target: 'current',
                domain: [['vehicle_id', '=', parseInt($("#vehicle_id").val())]],
            });
    },

    cancel_scan: function(e) {
        var self = this;
        $("#barcode_unmatched").hide();
        $("#barcode_matched").hide();
        $('.o_barcode_fleet_services_scan').show();
        $('.o_fleet_services_kiosk_mode').show();
        $("#discrepancy_created").hide();
        $(".barcode_field").val('').focus();
    },

});

core.action_registry.add('fleet_services_kanban', FleetServicesKanban);
return FleetServicesKanban;
});
