# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RecurringServicePlan(models.Model):
    """Recurring Service Plan

    """
    _name = 'recurring.service.plan'
    _description = 'Recurring Service Plan'
    _rec_name = "name"

    name = fields.Char(string='Recurring Service Plan',
                       default=_('New'), copy=False, required=True)
    interval_type = fields.Selection([
        ('vehicle_flight_hours', 'Vehicle Flight Hours')
    ], string='Interval Type', required=True)
    apply_vehicle_matching = fields.Selection([
        ('make_value', 'Make Value'),
        ('model_value', 'Model Value')
    ], string='Apply to Vehicle Matching')
    make_value_id = fields.Many2one(
        'fleet.vehicle.model.brand',
        string='Make Value', track_visibility='onchange')
    model_value_id = fields.Many2one(
        'fleet.vehicle.model',
        string='Model Value', track_visibility='onchange')
    interval_threshold = fields.Integer(string='Interval Threshold')
    interval_hours = fields.Integer(string='Interval Hours')
    vehicle_ids = fields.Many2many(
        'fleet.vehicle', 'recurring_service_plan_id',
        string='Applicable Vehicles')
    services_request_template_id = fields.Many2one(
        'service.request.template', string='Service Request Template',
        track_visibility='onchange')
    display_1 = fields.Boolean(string="Display 1", copy=False)
    display_2 = fields.Boolean(string="Display 2", copy=False)
    vehicle_recurring_service_history_ids = fields.One2many(
        'vehicle.recurring.service.history', 'recurring_service_plan_id',
        copy=False, string='Recurring Service History')
    parent_recurring_service_plan_id = fields.Many2one(
        'recurring.service.plan', copy=False, track_visibility='onchange',
        string='Parent Recurring Service Plan')
    child_plan_ids = fields.One2many(
        'recurring.service.plan', 'parent_recurring_service_plan_id',
        string='Sub Recurring Services')

    @api.constrains('display_1', 'display_2')
    def _check_display_flags(self):
        """Constrain: Display 1 and Display 2

        :return: None
        :raise: UserError if both boolean checked
        """
        plan = False
        if self.display_1:
            plan = self.search([
                ('id', '!=', self.id),
                ('display_1', '=', True),
            ], limit=1)
        elif self.display_2:
            plan = self.search([
                ('id', '!=', self.id),
                ('display_2', '=', True),
            ], limit=1)
        if plan:
            display = 'Display 1' if self.display_1 else 'Display 2'
            raise UserError(_(
                "%s Recurring Service Plan has already been marked as "
                "'%s.' You must first un-assign that plan's '%s' field prior "
                "to assigning this plan as the '%s' plan."
            ) % (plan.name, display, display, display))

    @api.onchange('apply_vehicle_matching')
    def onchange_stage_id(self):
        """
        For flush the value on m2o fields on selection.
        :return: None
        """
        for service_template in self:
            if service_template.apply_vehicle_matching == 'make_value':
                service_template.model_value_id = False
            elif service_template.apply_vehicle_matching == 'model_value':
                service_template.make_value_id = False

    @api.model
    def creation_service_request(self, vehicle_id, parent_plan=False):
        """Creation of service request.

        :param vehicle_id:
        :param parent_plan:
        :return: None
        """
        sr = self.env['vehicle.services'].new({
            'vehicle_id': vehicle_id.id,
            'vehicle_number': vehicle_id.license_plate,
            'x_location': vehicle_id.x_location,
            'x_flight_hours': vehicle_id.x_flight_hours,
            'sr_template_id': self.services_request_template_id.id,
            'images_ids': self.services_request_template_id.images_ids and [
                (6, 0, self.services_request_template_id.images_ids.ids)
            ] or False,
            'x_availability': vehicle_id.x_availability and
            vehicle_id.x_availability.id or False,
            'recurring_service_plan_id': self.id
        })
        sr.onchange_vehicle_id()
        sr._onchange_sr_template_id()
        sr._update_stage_id_priority()
        sr.create(sr._convert_to_write({key: sr[key] for key in sr._cache}))
        if parent_plan:
            self.create_sub_plan_history(vehicle_id)

    def verify_to_create(self, vehicle):
        """Verify TO Create.

        :param vehicle: Vehicle
        :return: Boolean
        """

        last = self.vehicle_recurring_service_history_ids.filtered(
            lambda vh: vh.vehicle_id == vehicle
        )
        if not last:
            return False
        return vehicle.x_flight_hours >= vehicle.last_generated_hours and \
            vehicle.x_flight_hours >= last[0].hours_till_next_generation

    @api.model
    def check_service_requests(self, vehicle_recs, parent_plan=False):
        """Check Service Requests

        Check validations for creation of service request.

        :param vehicle_recs: Vehicle(s)
        :param parent_plan: Boolean
        :return: None
        """
        parent = self.parent_recurring_service_plan_id
        is_parent_executed = False
        if parent and not parent_plan and parent.services_request_template_id:
            vehicle = parent.get_plan_vehicles()
            is_parent_executed = parent.check_service_requests(
                vehicle, parent_plan=True)
        if not vehicle_recs:
            return False
        vhcl_service = self.env['vehicle.services']
        service_history = self.env['vehicle.recurring.service.history']
        for vehicle_id in vehicle_recs:
            if not self.verify_to_create(vehicle_id):
                continue
            vehicle_service = vhcl_service.search([
                ('vehicle_id', '=', vehicle_id.id),
                ('recurring_service_plan_id', '=', self.id),
            ], order='id DESC')
            if not vehicle_service:
                self.creation_service_request(vehicle_id, parent_plan)
                continue
            remaining = vehicle_service.filtered(
                lambda sr: not sr.stage_id.final_stage
            )
            if remaining:
                remaining.write({
                    'x_flight_hours': vehicle_id.x_flight_hours
                })
                remaining.vehicle_id.last_generated_hours = \
                    vehicle_id.x_flight_hours
                if not is_parent_executed:
                    service_history.create(
                        self._prepare_recurring_plan_history_line(vehicle_id))
                if parent_plan:
                    self.create_sub_plan_history(vehicle_id)
            else:
                self.creation_service_request(vehicle_id, parent_plan)
        return True

    def get_plan_vehicles(self):
        """

        :return: Vehicle Recordset
        """
        fleet_vehicle = self.env['fleet.vehicle']
        vehicle_recs = self.vehicle_ids
        if self.apply_vehicle_matching == 'make_value':
            # Apply matching is set to make_value(vehicles will
            # search by brand which mentioned in model of vehicle)
            vehicle_recs = self.search([
                ('model_id.brand_id', '=', self.make_value_id.id)
            ])
        elif self.apply_vehicle_matching == 'model_value':
            # Apply matching is set to model_value(
            # vehicles will search by model)
            vehicle_recs = fleet_vehicle.search([
                ('model_id', '=', self.model_value_id.id)
            ])
        return vehicle_recs

    @api.model
    def _cron_generate_services(self):
        """ Cron Job: Generate Services

        For generate vehicle services on scheduler run.

        :return: None
        """
        recurring_service_plan_recs = self.search([
            ('services_request_template_id', '!=', False)
        ])
        if recurring_service_plan_recs:
            for record in recurring_service_plan_recs:
                record.check_service_requests(record.get_plan_vehicles())

    def create_sub_plan_history(self, vehicle):
        """

        :param vehicle:
        :return:
        """
        history = self.env['vehicle.recurring.service.history']
        for res in self.child_plan_ids:
            if vehicle not in res.vehicle_ids:
                continue
            history.create(res._prepare_recurring_plan_history_line(vehicle))

    def _prepare_recurring_plan_history_line(self, vehicles):
        """

        :param vehicles:
        :return:
        """
        lines = []
        interval = self.interval_hours - self.interval_threshold
        for vehicle in vehicles:
            lines.append({
                'vehicle_id': vehicle.id,
                'recurring_service_plan_id': self.id,
                'interval_threshold': self.interval_threshold,
                'interval_hours': self.interval_hours,
                'last_generated_hours': vehicle.x_flight_hours,
                'hours_till_next_generation':
                    vehicle.x_flight_hours + interval,
                'hours_till_next_generation_without_threshold': interval,
                'services_request_template_id':
                    self.services_request_template_id.id,
            })
        return lines

    def _prepare_recurring_plan_history(self, vehicle):
        """

        :param vehicle: Vehicle IDS
        :return: List of Dictionaries
        """
        return self._prepare_recurring_plan_history_line(
            self.env['fleet.vehicle'].browse(vehicle))

    @api.model
    def create(self, vals):
        """ORM: Create.

        Create and update the last generated at vehicle recurring service
        history whenever a new vehicle is assigned to a recurring service.

        :param vals: Values to create new record(s).
        :return: Super Call
        """
        res = super(RecurringServicePlan, self).create(vals)
        if vals.get('vehicle_ids'):
            self.env['vehicle.recurring.service.history'].create(
                res._prepare_recurring_plan_history(vals['vehicle_ids'][0][-1])
            )
        return res

    def write(self, vals):
        """ORM: Write.

        Create and update the last generated at vehicle recurring service
        history whenever a new vehicle is assigned to a recurring service.

        :param vals: Updated values
        :return: Super Call
        """
        if vals.get('vehicle_ids'):
            newly_add_vehicles = list(
                set(vals['vehicle_ids'][0][-1]) - set(self.vehicle_ids.ids))
            self.env['vehicle.recurring.service.history'].create(
                self._prepare_recurring_plan_history(newly_add_vehicles)
            )
        return super(RecurringServicePlan, self).write(vals)
