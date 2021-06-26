# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class ApplyMultipleVehicleWizard(models.TransientModel):
    """

    """
    _name = "apply.multiple.vehicle.wiz"
    _description = "Apply Service to Multiple Vehicle Wizard"

    vehicle_ids = fields.Many2many("fleet.vehicle", string="Vehicles")

    def create_multiple_vehicle_services(self):
        """Create selected service(2) for selected vehicle(s)

        User can use exist service(s) to create service(s) for selected
        vehicle(s).

        create_mutli_vehicle_sr method of Vehicle Service object is used to it,
        just pass the selected vehicle(s).

        FYI: Need to do loop on existing service(s), because copy method
        returns the error for singleton error with default values and also
        need to call some methods of SR to set default values of vehicle and
        template onchange methods.

        :return: None
        """
        active_model = self._context.get('active_model', False)
        active_ids = self._context.get('active_ids', False)
        if active_model and active_ids:
            existing_service = self.env[active_model].browse(active_ids)
            for service in existing_service:
                service.create_multi_vehicle_sr(self.vehicle_ids)
