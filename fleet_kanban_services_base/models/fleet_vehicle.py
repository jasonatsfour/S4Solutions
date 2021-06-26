# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from datetime import datetime

import dateutil.parser
import pytz
from odoo import models, fields, api

from .assets import return_action_to_open


class FleetVehicle(models.Model):
    """

    """
    _inherit = 'fleet.vehicle'

    fleet_service_count = fields.Float(compute='_compute_count_all')
    fleet_repair_count = fields.Float(compute='_compute_count_repair')
    fleet_recurring_plan_service_count = fields.Float(
        compute='_compute_count_recurring_plan_services')
    x_flight_hours = fields.Float(string='Flight Hours',
                                  track_visibility='onchange')
    recurring_service_plan_id = fields.Many2one(
        "recurring.service.plan", string="Recurring Service Plan")
    product_id = fields.Many2one("product.product", string="Product")
    vehicle_status_id = fields.Many2one("fleet.vehicle.status",
                                        string="Vehicle Status")
    x_availability = fields.Many2one("fleet.vehicle.available",
                                     string="Availability")
    x_location = fields.Many2one("stock.location",
                                 string="Other Location")
    x_hw_config = fields.Char(string="HW Version",
                              track_visibility='onchange')
    x_serial_no = fields.Char(string="Serial #")
    vehicle_recurring_service_history_ids = fields.One2many(
        'vehicle.recurring.service.history', 'vehicle_id',
        copy=False, string='Vehicle Recurring Service History')
    last_generated_hours = fields.Float(string='Last Generated At Hours')
    color_index = fields.Integer('Color Index', related='x_availability.color')

    @api.model
    def match_barcode(self, license_plate):
        """

        Function call for match license plate number data.

        :param license_plate:
        :return:
        """
        flt_vh_rec = self.search([
            ('license_plate', '=', license_plate)
        ])
        if not flt_vh_rec:
            return False
        vehicle_discrepancy_type_rec = self.env[
            'vehicle.discrepancy.type'].search([]).mapped('name')
        vehicle_observed_during_rec = self.env[
            'observed.during'].search([]).mapped('name')
        vehicle_hw_failure_mode_rec = self.env[
            'hw.failure.mode'].search([]).mapped('name')
        return {
            'vehicle_id': flt_vh_rec.id,
            'fleet_vehicle_number': flt_vh_rec.license_plate,
            'x_location': flt_vh_rec.x_location and
                          flt_vh_rec.x_location.name or '',
            'x_location_id': flt_vh_rec.x_location and
                             flt_vh_rec.x_location.id or '',
            'x_flight_hours': flt_vh_rec.x_flight_hours,
            'x_hw_config': flt_vh_rec.x_hw_config,
            'vehicle_status_rec': flt_vh_rec.x_availability.name or '',
            'vehicle_discrepancy_type_rec': vehicle_discrepancy_type_rec,
            'vehicle_observed_during_rec': vehicle_observed_during_rec,
            'vehicle_hw_failure_mode_rec': vehicle_hw_failure_mode_rec
        }

    @api.model
    def confirm_vehicle_discrepancy(self, vehicle_discrepancy_data):
        """

        :param vehicle_discrepancy_data:
        :return:
        """
        attachment_ids = []
        critical_selection = False
        active_tz = pytz.timezone(self._context.get("tz", "UTC"))
        if self.env.user.tz:
            active_tz = pytz.timezone(self.env.user.tz)
        if vehicle_discrepancy_data:
            ir_attach = self.env['ir.attachment']
            vehicle_service = self.env['vehicle.services']
            hw_fail_md = self.env['hw.failure.mode']
            vh_disc = self.env['vehicle.discrepancy']
            obs_dur = self.env['observed.during']
            avail = self.env['fleet.vehicle.available'].search([])
            state_available = {
                'Available': avail.filtered(lambda l: l.is_available)[0].id,
                'Grounded': avail.filtered(lambda l: l.is_grounded)[0].id,
                'In Work': avail.filtered(lambda l: l.is_in_repair)[0].id
            }
            vehicle_rec = {}
            for vh_discrepancy in vehicle_discrepancy_data:
                if vh_discrepancy and \
                        'attachment_ids' in vh_discrepancy:
                    for attachment in vh_discrepancy.get('attachment_ids'):
                        attachment_id = ir_attach.create({
                            'name': attachment.get('name'),
                            'type': 'binary',
                            'db_datas': attachment.get('data'),
                            'datas': attachment.get('data')
                        })
                        attachment_ids.append(attachment_id.id)
                if vh_discrepancy.get('priority') == 'critical':
                    critical_selection = 'yes'
                if vh_discrepancy.get('observed_date'):
                    observed_datetime_format = dateutil.parser.parse(
                        vh_discrepancy.get('observed_date'))
                else:
                    observed_datetime_format = 0
                # Convert observed_datetime to UTC
                utc_observed_datetime = active_tz.localize(datetime.strptime(
                    str(observed_datetime_format), '%Y-%m-%d %H:%M:%S')
                ).astimezone(pytz.UTC)
                hw_failure_mode_ids = []
                if 'hw_failure_mode' in vh_discrepancy and \
                        vh_discrepancy.get('hw_failure_mode', False):
                    hw_failure_mode_ids = [(6, 0, hw_fail_md.search([
                        ('name', 'in', vh_discrepancy['hw_failure_mode'])
                    ]).ids)]

                vh_discrepancy['x_availability'] = state_available.get(
                    vh_discrepancy['x_availability'], False)

                new_discr = vh_disc.create({
                    'vehicle_id': vh_discrepancy.get('vehicle_id'),
                    'vehicle_number': vh_discrepancy.get('vehicle_number'),
                    'title': vh_discrepancy.get('title'),
                    'x_location': vh_discrepancy.get('x_location_id'),
                    'observed_date': utc_observed_datetime.
                        strftime('%Y-%m-%d %H:%M:%S'),
                    'x_flight_hours': vh_discrepancy.get('x_flight_hours', 0),
                    'x_hw_config': vh_discrepancy.get('x_hw_config', 0),
                    'observed_during': obs_dur.search([
                        ('name', '=', vh_discrepancy.get('observed_during'))
                    ], limit=1).id or 0,
                    'hw_failure_mode_ids': hw_failure_mode_ids,
                    'x_availability': vh_discrepancy.get('x_availability'),
                    'description': vh_discrepancy.get('description') or 0,
                    'priority': vh_discrepancy.get('priority'),
                    'critical_selection': critical_selection,
                    'images_ids': [(6, 0, attachment_ids)]
                })
                vehicle_services_rec = vehicle_service.search([
                    ('vehicle_discrepancy_id', '=', new_discr.id)
                ])
                vehicle_services_rec.onchange_vehicle_id()
                vehicle_rec = {
                    'vehicle_discrepancy_id': new_discr.id,
                    'discrepancy_barcode': new_discr.vehicle_number,
                    'vehicle_discrepancy_name': new_discr.name,
                    'x_availability': new_discr.x_availability.id,
                    'vehicle_services_id': vehicle_services_rec.id,
                    'vehicle_services_name': vehicle_services_rec.name,
                    'observed_date': utc_observed_datetime.
                    strftime('%Y-%m-%d %H:%M:%S'),
                }
            return vehicle_rec

    def _compute_count_all(self):
        """

        :return:
        """
        super(FleetVehicle, self)._compute_count_all()
        flt_service = self.env['vehicle.services']
        for record in self:
            record.fleet_service_count = flt_service.search_count([
                ('vehicle_id', '=', record.id),
                ('stage_id.final_stage', '=', False)
            ])

    def _compute_count_repair(self):
        """

        :return:
        """
        flt_repair = self.env['fleet.repair']
        for record in self:
            record.fleet_repair_count = flt_repair.search_count([
                ('vehicle_id', '=', record.id),
                ('stage_id.final_stage', '=', False)
            ])

    def _compute_count_recurring_plan_services(self):
        """

        :return:
        """
        flt_service = self.env['vehicle.services']
        for record in self:
            record.fleet_recurring_plan_service_count = flt_service. \
                search_count([
                    ('vehicle_id', '=', record.id),
                    ('recurring_service_plan_id', '!=', False),
                    ('stage_id.final_stage', '=', False)
                ])

    def return_action_to_open_repair(self):
        """
        This opens the xml view specified in xml_id for the current vehicle.
        :return:
        """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            domain = [
                ('vehicle_id', '=', self.id),
                ('stage_id.final_stage', '=', False)
            ]
            return return_action_to_open(self, xml_id, domain)
        return False

    def return_action_to_open_service(self):
        """
        This opens the xml view specified in xml_id for the current vehicle.
        :return:
        """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            domain = [
                ('vehicle_id', '=', self.id),
                ('stage_id.final_stage', '=', False)
            ]
            return return_action_to_open(self, xml_id, domain)
        return False

    def return_action_to_open_recurring_plan_service(self):
        """
        This opens the xml view specified in xml_id for the current vehicle.
        :return:
        """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            domain = [
                ('vehicle_id', '=', self.id),
                ('recurring_service_plan_id', '!=', False),
                ('stage_id.final_stage', '=', False)
            ]
            return return_action_to_open(self, xml_id, domain)
        return False

    @api.model
    def deactivate_base_record_rule(self):
        """

        :return:
        """
        rule = self.env['ir.rule']
        model = self.env['ir.model']
        models = [
            'fleet.vehicle',
            'fleet.vehicle.log.contract',
            'fleet.vehicle.cost',
            'fleet.vehicle.log.services',
            'fleet.vehicle.odometer',
            'fleet.vehicle.log.fuel',
            'fleet.vehicle'
        ]
        domain = [
            "[('driver_id','=',user.partner_id.id)]",
            "[('cost_id.vehicle_id.driver_id','=',user.partner_id.id)]",
            "[('vehicle_id.driver_id','=',user.partner_id.id)]"
        ]
        for model_name in models:
            model_id = model.search([('model', '=', model_name)])
            if model_id:
                vehicle_rule = rule.sudo().search([
                    ('model_id', '=', model_id.id),
                    ('domain_force', 'in', domain),
                    ('active', '=', True)
                ])
                vehicle_rule.sudo().write({'active': False})

    def _prepare_vehicle_details(self):
        """

        :return:
        """
        return {
            'vehicle_number': self.license_plate,
            'x_location': self.x_location and self.x_location.id or False,
            'x_flight_hours': self.x_flight_hours,
            'x_serial_no': self.x_serial_no,
            'x_hw_config': self.x_hw_config,
            'x_availability': self.x_availability.id
        }
