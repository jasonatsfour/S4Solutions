# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models, fields


class VehicleServices(models.Model):
    """Inherited: Vehicle Services

    """
    _inherit = 'vehicle.services'

    def write(self, vals):
        """ORM: Write

        Override Create Method to add service sequence.

        :param vals:
        :return:
        """
        res = super(VehicleServices, self).write(vals)
        rec = self.recurring_service_plan_id
        if self.vehicle_id and self.stage_id.final_stage and \
                rec and rec.interval_type == 'vehicle_flight_et':
            self.vehicle_id.last_sr_id = self.id
            self.vehicle_id.last_sr_date = fields.Date.today()
        return res
