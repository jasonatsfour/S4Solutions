# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import api, fields, models


class FleetRepairService(models.Model):
    """

    """
    _name = 'fleet.repair.service'
    _description = 'Fleet Repair Service'

    service_id = fields.Many2one('vehicle.services', string="Service Request")
    title = fields.Char('Title', related='service_id.title')
    stage_id = fields.Many2one(
        "vehicle.service.state", string="Vehicle Status",
        related='service_id.stage_id', store=True, readonly=False)
    repair_id = fields.Many2one('fleet.repair', string="Repair")

    @api.onchange('stage_id')
    def onchange_stage_id(self):
        """

        :return:
        """
        service_state_rec = self.env['vehicle.service.state'].search([
            ('final_stage', '=', True)
        ], limit=1)
        grounded_services = self.env['vehicle.services'].search([
            ('vehicle_id', '=', self.service_id.vehicle_id.id),
            ('priority', '=', 'critical'),
            ('stage_id', '!=', service_state_rec.id)
        ])
        vehicle_available = self.env['fleet.vehicle.available']
        vehicle_stage_grounded = vehicle_available.search([
            ('is_grounded', '=', True)
        ], limit=1)
        vehicle_stage_available = vehicle_available.search([
            ('is_available', '=', True)
        ], limit=1)

        x_availability = False
        if self.service_id.priority == 'critical' and \
                len(grounded_services) > 1:
            x_availability = vehicle_stage_grounded.id
        elif self.service_id.priority == 'critical' and \
                len(grounded_services) == 1:
            if not self.stage_id.final_stage:
                x_availability = vehicle_stage_grounded.id
            elif self.stage_id.final_stage:
                x_availability = vehicle_stage_available.id
        elif self.service_id.priority == 'critical' and \
                len(grounded_services) == 0:
            if not self.stage_id.final_stage:
                x_availability = vehicle_stage_grounded.id
            elif self.stage_id.final_stage:
                x_availability = vehicle_stage_available.id
        elif self.service_id.priority == 'non-critical':
            if len(grounded_services) >= 1:
                x_availability = vehicle_stage_grounded.id
            else:
                x_availability = vehicle_stage_available.id
        self.service_id.vehicle_id.write({
            'x_availability': x_availability
        })
