# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api


class FleetVehicleCost(models.Model):
    """

    """
    _inherit = 'fleet.vehicle.cost'

    vehicle_services_id = fields.Many2one(
        'vehicle.services', string='Vehicle Services')
    services_request_template_id = fields.Many2one(
        'service.request.template', string='Vehicle Services Template')
    repair_id = fields.Many2one('fleet.repair', string='Repair')
    stage_id = fields.Many2one(
        'fleet.repair.stage', string='Stage',
        track_visibility='onchange', related='repair_id.stage_id')
    last_update_date = fields.Date(string='Last Update Date', store=True)
    last_update_user_id = fields.Many2one('res.users',
                                          string='User', store=True)
    x_serial_no = fields.Char(string="Serial #",
                              related="vehicle_id.x_serial_no")
    x_completed_by = fields.Many2one('res.users', string='Completed By')

    @api.model
    def create(self, vals):
        """

        :param vals:
        :return:
        """
        if 'vehicle_services_id' in vals:
            vehicle_service_id = self.env['vehicle.services'].browse(
                vals['vehicle_services_id'])
            vals.update({'vehicle_id': vehicle_service_id.vehicle_id.id})
        if 'repair_id' in vals:
            repair_id = self.env['fleet.repair'].browse(vals['repair_id'])
            vals.update({'vehicle_id': repair_id.vehicle_id.id})
        return super(FleetVehicleCost, self).create(vals)
