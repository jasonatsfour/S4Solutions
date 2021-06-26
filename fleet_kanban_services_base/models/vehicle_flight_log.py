# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class VehicleFlightLog(models.Model):
    """

    """
    _name = 'vehicle.flight.log'
    _description = 'Vehicle Flight Log'

    def name_get(self):
        """

        :return:
        """
        result = []
        for vehicle in self:
            if vehicle.date:
                name = vehicle.vehicle_id.name + '/' + str(vehicle.date)
            else:
                name = vehicle.vehicle_id.name + '/'
            result.append((vehicle.id, name))
        return result

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    flight_hours = fields.Float(string='Flights Hours')
    date = fields.Date(string='Date')
    flight_count = fields.Integer(string='Flight Count')
    flight_id = fields.Char(string='Flight ID')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.user.company_id)
