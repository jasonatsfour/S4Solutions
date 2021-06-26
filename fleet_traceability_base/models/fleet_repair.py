# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import _, api, fields, models


class FleetRepairType(models.Model):
    """Inherit Fleet Kanban Services Base: Fleet Repair Type.

    Set flag Is As-Maintained? to separate from other type.
    """
    _inherit = 'fleet.repair.type'

    is_as_maintained = fields.Boolean(string='Is As-Maintained?')


class FleetRepair(models.Model):
    """Inherit Fleet Kanban Services Base: Fleet Repair.

    Fields:
    product_id: Override to make related false.
    lot_id: To set Serial/Lot of product to repair.
    is_as_maintained: Related of Repair Type.

    Methods:
    onchange_vehicle_lot: -> Vehicle and Lot
    onchange_vehicle_id: -> Vehicle
    """
    _inherit = 'fleet.repair'

    # override this field to set the related as false.
    product_id = fields.Many2one(
        'product.product', string='Product to Repair', related=False)
    is_as_maintained = fields.Boolean(
        string='Is As-Maintained', related='type_id.is_as_maintained')
    lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial')

    @api.onchange('vehicle_id', 'lot_id')
    def onchange_vehicle_lot(self):
        """On Change Vehicle Lot.

        To setup Location of either from vehicle or lot and set product
        if there is not product but lot is specified.

        :return: None
        """
        if self.vehicle_id and self.vehicle_id.x_location:
            self.x_location = self.vehicle_id.x_location.id
        elif self.lot_id and self.lot_id.location_id:
            self.x_location = self.lot_id.location_id.id

        if self.lot_id and not self.product_id:
            self.product_id = self.lot_id.product_id.id

    @api.onchange('vehicle_id')
    def onchange_vehicle_id(self):
        """Override: Fleet Kanban Services Base: On Change Vehicle.

        On change of vehicle on repair, it will check for vehicle product and
        lot and set them to repair.
        But if any one is missing then it will RETURN Warning.

        Warning: No Product & Lot Serial Number!

        :return: None or RETURN Warning
        """
        for repair in self:
            if repair.vehicle_id:
                if repair.vehicle_id.product_id and repair.vehicle_id.lot_id:
                    repair.product_id = repair.vehicle_id.product_id
                    repair.lot_id = repair.vehicle_id.lot_id
                    repair.x_serial_no = repair.vehicle_id.x_serial_no
                else:
                    repair.product_id = False
                    repair.lot_id = False
                    repair.x_serial_no = False
                    return {
                        'warning': {
                            'title': _('No Product & Lot Serial Number!'),
                            'message': _(
                                "This vehicle '%s' does not have "
                                "its product and lot serial number."
                            ) % repair.vehicle_id.license_plate
                        }}

    @api.onchange('stage_id')
    def onchange_stage_id(self):
        """Override: Onchange Stage

        After completing basic process, here it will checks for
        the operation type and bases on that manage installed location
        of serial/lot number along with state by calling calculate_lot_status.

        :return: None or Raise User Error
        """
        res = super(FleetRepair, self).onchange_stage_id()
        for repair in self.filtered(
                lambda r: r.stage_id.final_stage and r.lot_id):
            for operation in repair.operations.filtered(
                    lambda op: op.type in ['add', 'remove']
            ):
                operation.lot_id.write({
                    'lot_ids': [
                        (4 if operation.type == 'add' else 3,
                         operation.origin_part_of_id and
                         operation.origin_part_of_id.id or repair.lot_id.id)
                    ],
                    'is_none_production': operation.type == 'remove'
                })
                operation.lot_id.calculate_lot_status(
                    operation.location_dest_id.id
                    if operation.type == 'add' else operation.location_id.id)
        return res

    @api.onchange('product_id', 'lot_id')
    def _onchange_product_lot(self):
        """Onchange: Product or Serial/Lot number.

        To find vehicle as per product and serial/lot selection.

        :return: None
        """
        vehicle = self.env['fleet.vehicle']
        for res in self:
            if res.product_id and res.lot_id and not res.vehicle_id:
                res.vehicle_id = vehicle.search([
                    ('product_id', '=', res.product_id.id),
                    ('lot_id', '=', res.lot_id.id)
                ], limit=1)
                res.x_serial_no = res.vehicle_id.x_serial_no

    def create_operation_as_maintained_history(self, lot_id, lot_version):
        """Create Operation AS-Maintained History

        To log history of every operation of current repair.

        :param lot_id: Lot number of the product that is going to maintenance.
        :param lot_version: Lot Version.
        :return: None.
        """
        for line in self.operations:
            line.create_fleet_repair_as_maintained_history(lot_id, lot_version)

    def write(self, vals):
        """ORM: Write

        Override to update the lot_version of lot_serial_number.

        :param vals: Received values in dictionary format
        :return: None
        """
        res = super(FleetRepair, self).write(vals)
        if vals.get('stage_id', False) and self.stage_id.final_stage:
            version = self.lot_id.lot_version + 1
            self.create_operation_as_maintained_history(self.lot_id, version)
            self.lot_id.onchange_lot_version()
        return res

    def action_make_all_done(self):
        """

        Override this method to add the edit logic, if operation type is edit.

        :return: Boolean
        """
        for repair in self:
            repair._check_repair_product()
            repair.operations.action_make_done()
        return True

    @api.model
    def selected_lot_details(self, lot_number):
        """Selected Lot Details

        It will call from the JS to get Serial/Lot name to display on screen.

        :param lot_number: Dictionary with lot id
        :return: Dictionary only with Lot name
        """
        return {
            'lot_name': self.env['stock.production.lot'].search([
                ('id', '=', lot_number.get('id'))
            ], limit=1).name
        }

    @api.model
    def selected_non_lot_details(self, lot_number):
        """Selected Non Lot Details

        It will call from the JS to get Serial/Lot name to display on screen.

        :param lot_number: Dictionary with lot id
        :return: Dictionary only with Lot name
        """
        return {
            'lot_name': self.env['stock.production.quant'].search([
                ('id', '=', lot_number.get('id'))
            ], limit=1).name
        }

    def _get_root_vehicle_location(self, parent_lot):
        """Root Vehicle and Location

        Using given lot, it finds the root parent serial/lot to manage version
        with repair line also return vehicle and manage location from root
        serial/lot number.

        :param parent_lot: Parent Product Serial/Lot of As-Maintained Screen
        :return: Root Lot and Location along with Vehicle
        """
        root_lot = parent_lot.get_root_lot()
        vehicle_id = self.env['fleet.vehicle'].search([
            ('product_id', '=', root_lot.product_id.id),
            ('lot_id', '=', root_lot.id)
        ], limit=1)
        repair_loc = False
        if vehicle_id.x_location:
            repair_loc = vehicle_id.x_location.id
        elif root_lot.location_id:
            repair_loc = root_lot.location_id.id
        elif parent_lot.location_id:
            repair_loc = parent_lot.location_id.id
        return root_lot, repair_loc, vehicle_id

    @api.model
    def add_remove_lot_serial_number(self, lot_details):
        """ Add/Remove Serial/Lot number using As-Maintained Screen.

        Any operation that perform from as_maintained structure for lot_serial.

        :param lot_details:
        :return:
        """
        prdc_lot = self.env['stock.production.lot']
        repair_line = self.env['fleet.repair.line']
        parent_lot_rec = prdc_lot.browse(lot_details.get('parent_lot_number'))
        root_lot, repair_loc, vehicle_id = self._get_root_vehicle_location(
            parent_lot_rec)
        if not repair_loc:
            return _('No repair location.')
        final_stage_rec = self.env['fleet.repair.stage'].search([
            ('final_stage', '=', True)
        ], limit=1)
        fleet_repair_type_id = self.env['fleet.repair.type'].search([
            ('is_as_maintained', '=', True)
        ], limit=1)
        operation_type = lot_details.get('operation', False)
        fleet_repair_rec = self.create({
            'vehicle_id': vehicle_id.id or False,
            'product_id': root_lot.product_id.id,
            'lot_id': root_lot.id,
            'type_id': fleet_repair_type_id.id or False,
            'x_location': repair_loc,
            'x_serial_no': vehicle_id.x_serial_no,
        })
        lot_recs = prdc_lot.browse(lot_details.get('current_lot_number'))
        fleet_repair_line = repair_line.new({
            'type': operation_type,
            'product_id': lot_recs.product_id.id,
            'lot_id': lot_recs.id,
            'repair_id': fleet_repair_rec.id,
            'price_unit': 0.0,
            'product_uom': 1,
            'product_uom_qty': 1,
            'origin_part_of_id': parent_lot_rec.id,
            'replacement_lot_id': lot_details.get('selected_lot_number', False)
        })
        fleet_repair_line.refurbish()
        vals = fleet_repair_line._convert_to_write({
            name: fleet_repair_line[name]
            for name in fleet_repair_line._cache
        })
        fleet_repair_line_rec = repair_line.create(vals)
        fleet_repair_line_rec.action_make_done()
        fleet_repair_rec.stage_id = final_stage_rec.id
        fleet_repair_rec.onchange_stage_id()

    @api.model
    def add_remove_non_traceable_lot(self, lot_details):
        """Add/Remove Non Traceable Lot

        This method is for any operation that perform from As-Maintained
        structure for Non traceable entries.

        :param lot_details:
        :return:
        """
        production_lot = self.env['stock.production.lot']
        parent_lot = production_lot.browse(
            lot_details.get('parent_lot_number'))
        prdc_quant = self.env['stock.production.quant']
        current_lot = production_lot.browse(
            lot_details.get('current_lot_number'))
        operation = lot_details.get('operation')
        if operation in ['add', 'remove']:
            current_lot.update({
                'lot_ids': [(4 if operation == 'add' else 3, parent_lot.id)]
            })
        # if current_lot is non_traceable
        if operation == 'edit':
            selected_lot_rec = prdc_quant.search([
                ('name', '=', lot_details.get('selected_lot_number'))
            ])
            if not current_lot:
                selected_lot_rec.update({
                    'lot_ids': [(4, parent_lot.id)]
                })
                current_lot.update({
                    'lot_ids': [(3, parent_lot.id)]
                })
            else:
                # if current_lot is traceable
                final_stage_rec = self.env['fleet.repair.stage'].search([
                    ('final_stage', '=', True)
                ], limit=1)
                fleet_repair_type_id = self.env['fleet.repair.type'].search([
                    ('is_as_maintained', '=', True)
                ], limit=1)
                (
                    root_lot, repair_loc, vehicle_id
                ) = self._get_root_vehicle_location(
                    parent_lot)
                if not repair_loc:
                    return _('No repair location.')
                fleet_repair_rec = self.create({
                    'vehicle_id': vehicle_id.id or '',
                    'product_id': root_lot.product_id.id,
                    'lot_id': root_lot.id,
                    'type_id': fleet_repair_type_id.id or '',
                    'x_location': repair_loc,
                })
                repair_line = self.env['fleet.repair.line']
                fleet_repair_line = repair_line.new({
                    'product_id': current_lot.product_id.id,
                    'lot_id': current_lot.id,
                    'repair_id': fleet_repair_rec.id,
                    'price_unit': 0.0,
                    'product_uom': 1,
                    'product_uom_qty': 1,
                    'type': 'remove',
                })
                fleet_repair_line.refurbish()
                vals = fleet_repair_line._convert_to_write({
                    name: fleet_repair_line[name]
                    for name in fleet_repair_line._cache
                })
                fleet_repair_line = repair_line.create(vals)
                # to make fleet_repair_line as mark done
                if fleet_repair_line.fleet_use:
                    fleet_repair_line.action_make_done()
                    if fleet_repair_line.stage == 'marked':
                        fleet_repair_rec.update({
                            'stage_id': final_stage_rec.id,
                            'operations': [(4, fleet_repair_line.id)],
                        })
                        fleet_repair_rec.lot_id.check_lot_status(
                            fleet_repair_rec, False)
                    if fleet_repair_line.type == 'remove' and \
                            fleet_repair_rec.stage_id.id == final_stage_rec.id:
                        # remove parent lot serial as
                        # installed location in selected lot
                        current_lot.calculate_lot_status(
                            fleet_repair_line.location_dest_id.id)
                        current_lot.update({
                            'lot_ids': [(3, parent_lot.id)]
                        })
                        # add parent lot serial as
                        # installed location in selected lot
                        selected_lot_rec.update({
                            'lot_ids': [(4, parent_lot.id)]
                        })
