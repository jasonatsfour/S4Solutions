# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import api, models, fields


class VehicleServices(models.Model):
    """Inherit Fleet Kanban Services Base: Vehicle Services

    Fields:
    product_id: To set product to service.
    lot_id: Serial/Lot of respected product.

    Methods:
    onchange_vehicle_id: Override -> vehicle_id
    """
    _inherit = 'vehicle.services'

    product_id = fields.Many2one('product.product', string='Product')
    lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial')

    @api.onchange('vehicle_id')
    def onchange_vehicle_id(self):
        """Override: Fleet Kanban Services Base: On Change Vehicle ID
        Override this method to add the product and lot
        with respect to its vehicle.
        :return: None
        """
        for service in self:
            vehicle = service.vehicle_id
            service.vehicle_number = vehicle.license_plate
            service.x_location = vehicle.x_location and \
                                 vehicle.x_location.id or False
            service.x_flight_hours = vehicle.x_flight_hours
            service.x_availability = vehicle.x_availability and \
                                     vehicle.x_availability.id or False
            service.x_hw_config = vehicle.x_hw_config
            service.x_serial_no = vehicle.x_serial_no
            service.product_id = vehicle.product_id
            service.lot_id = vehicle.lot_id
