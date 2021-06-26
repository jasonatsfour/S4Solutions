# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

from .assets import return_action_to_open


class VehicleServices(models.Model):
    """Vehicle Service Request

    """
    _name = 'vehicle.services'
    _description = 'Vehicle Services'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date'

    name = fields.Char(string="Service Request", copy=False,
                       default=lambda self: _('New'))
    title = fields.Char(string='Title')
    vehicle_discrepancy_id = fields.Many2one(
        'vehicle.discrepancy', string="Vehicle Discrepancy", copy=False)
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    x_availability = fields.Many2one('fleet.vehicle.available',
                                     string="Availability")
    x_hw_config = fields.Char(string="HW Version",
                              track_visibility='onchange')
    x_serial_no = fields.Char(string="Serial #",
                              track_visibility='onchange')
    vehicle_number = fields.Char(string="Vehicle Number", store=True,
                                 track_visibility='onchange')
    type_id = fields.Many2one('vehicle.service.type', string="Type",
                              track_visibility='onchange')
    tag_ids = fields.Many2many('vehicle.service.tag', string="Tags")
    x_location = fields.Many2one('stock.location', string="Location")
    x_flight_hours = fields.Float(string="Flights Hours",
                                  track_visibility='onchange')
    observed_date = fields.Datetime(string="Observed Date", copy=False)
    deadline_date = fields.Datetime(string="Service Deadline", copy=False)
    discrepancy_type_id = fields.Many2one(
        'vehicle.discrepancy.type', string="Discrepancy Type", store=True,
        related='vehicle_discrepancy_id.discrepancy_type_id')
    description = fields.Text(string="Description", limit=500)
    images_ids = fields.Many2many('ir.attachment', string="Image")
    priority = fields.Selection([
        ('critical', 'Grounded'),
        ('non-critical', 'Non-Grounded')
    ], track_visibility='onchange', string='Grounding Status')
    included_services_ids = fields.One2many(
        'fleet.vehicle.cost', 'vehicle_services_id',
        string='Included Services')
    recurring = fields.Boolean(string='Recurring')
    repair_id = fields.Many2one('fleet.repair', "Repair")
    stage_id = fields.Many2one(
        'vehicle.service.state', ondelete='restrict', copy=False,
        group_expand='_read_group_stage_ids', track_visibility='onchange')
    is_draft = fields.Boolean(related='stage_id.is_draft')
    in_progress = fields.Boolean(related='stage_id.in_progress')
    final_stage = fields.Boolean(related='stage_id.final_stage')
    user_id = fields.Many2one('res.users', string="User")
    fleet_repair_count = fields.Integer(
        compute='_compute_fleet_repair_count', string='# of Vehicle Services')
    is_grounded = fields.Boolean(default=False)
    critical_selection = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], track_visibility='onchange')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.user.company_id)
    recurring_service_plan_id = fields.Many2one(
        'recurring.service.plan', string='Service Plan')
    active = fields.Boolean(
        default=True,
        help="Set active to false to hide the "
             "Vehicle service without removing it.")
    resolution = fields.Text(string="Resolution")
    is_resolution_required = fields.Boolean(string="Is Resolution Required?")
    operations = fields.One2many(
        'fleet.repair.line', 'service_request_id', string="Parts", copy=True)
    sr_template_id = fields.Many2one('service.request.template',
                                     string='SR Template')

    @api.model
    def default_get(self, fields):
        """

        :param fields:
        :return:
        """
        res = super(VehicleServices, self).default_get(fields)
        default_resolution = 'Resolution:'
        draft_stage = self.env['vehicle.service.state'].search([
            ('is_draft', '=', True)
        ], limit=1)
        if draft_stage:
            res.update({
                'stage_id': draft_stage.id,
                'resolution': default_resolution
            })
        return res

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """
        Read group customization in order to display all the stages of
        the Service in the Kanban view, even there is no Repair in that stage.
        :param stages:
        :param domain:
        :param order:
        :return:
        """
        stage_ids = stages._search(
            [], order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    def _update_stage_id_priority(self):
        """

        :return:
        """
        grounded_services = self.search([
            ('vehicle_id', '=', self.vehicle_id.id),
            ('priority', '=', 'critical'),
            ('stage_id.final_stage', '=', False)
        ])
        fleet_available_ref = self.env['fleet.vehicle.available']
        vehicle_stage_grounded = fleet_available_ref.search([
            ('is_grounded', '=', True)
        ], limit=1)
        vehicle_stage_available = fleet_available_ref.search([
            ('is_available', '=', True)
        ], limit=1)
        x_availability = False
        if self.priority == 'critical' and len(grounded_services) > 1:
            x_availability = vehicle_stage_grounded.id
        elif self.priority == 'critical' and len(grounded_services) == 1:
            if not self.stage_id.final_stage:
                x_availability = vehicle_stage_grounded.id
            elif self.stage_id.final_stage:
                x_availability = vehicle_stage_available.id
        elif self.priority == 'critical' and len(grounded_services) == 0:
            if not self.stage_id.final_stage:
                x_availability = vehicle_stage_grounded.id
            elif self.stage_id.final_stage:
                x_availability = vehicle_stage_available.id
        elif self.priority == 'non-critical':
            if len(grounded_services) >= 1:
                x_availability = vehicle_stage_grounded.id
            else:
                x_availability = vehicle_stage_available.id
        self.vehicle_id.write({
            'x_availability': x_availability
        })

    @api.onchange('stage_id')
    def onchange_stage_id(self):
        """

        :return:
        """
        self._update_stage_id_priority()

    @api.onchange('priority')
    def onchange_priority(self):
        """

        :return:
        """
        self._update_stage_id_priority()

    @api.onchange('vehicle_id')
    def onchange_vehicle_id(self):
        """

        :return:
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

    @api.onchange('vehicle_discrepancy_id')
    def onchange_vehicle_discrepancy_id(self):
        """

        :return:
        """
        for service in self:
            vh_discr = service.vehicle_discrepancy_id
            if vh_discr:
                service.vehicle_id = vh_discr.vehicle_id.id
                service.vehicle_number = vh_discr.vehicle_number
                service.x_location = vh_discr.x_location and \
                                     vh_discr.x_location.id or False
                service.x_flight_hours = vh_discr.x_flight_hours
                service.x_hw_config = vh_discr.x_hw_config
                service.x_serial_no = vh_discr.x_serial_no
                service.description = vh_discr.description
                service.images_ids = vh_discr.images_ids and [
                    (6, 0, vh_discr.images_ids.ids)] or False
                service.x_availability = vh_discr.vehicle_id.x_availability \
                                         and vh_discr.vehicle_id.x_availability.id or False

    def _prepare_recurring_plan_history(self):
        """

        :return: Dictionary
        """
        lines = []
        for res in self:
            recurring = res.recurring_service_plan_id
            interval = recurring.interval_hours - recurring.interval_threshold
            lines.append({
                'vehicle_id': res.vehicle_id.id,
                'recurring_service_plan_id': recurring.id,
                'interval_threshold': recurring.interval_threshold,
                'interval_hours': recurring.interval_hours,
                'last_generated_hours': res.vehicle_id.x_flight_hours,
                'hours_till_next_generation':
                    res.vehicle_id.x_flight_hours + interval,
                'hours_till_next_generation_without_threshold': interval,
                'services_request_template_id':
                    recurring.services_request_template_id.id,
            })
        return lines

    @api.model
    def create(self, vals):
        """
        Override Create Method to add service sequence.
        :param vals:
        :return:
        """
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'vehicle.services') or _('New')
        if vals.get('vehicle_id', False):
            vehicle_id = self.env['fleet.vehicle'].browse(vals['vehicle_id'])
            vals.update(vehicle_id._prepare_vehicle_details())
        res = super(VehicleServices, self).create(vals)
        if 'sr_template_id' in vals:
            res.update_for_sr_template()
        if 'recurring_service_plan_id' in vals:
            self.env['vehicle.recurring.service.history'].create(
                res._prepare_recurring_plan_history()
            )
            res.vehicle_id.last_generated_hours = res.x_flight_hours
        return res

    def update_for_sr_template(self):
        """Copy data from SR Template.

        :return: None
        """
        self.create_fleet_repair_lines()
        self.create_included_services()
        self.create_template_images()

    def write(self, vals):
        """
        Override Create Method to add service sequence.

        :param vals:
        :return: None or Raise Error
        :raise: Validation Error
        """
        if 'stage_id' in vals and self.stage_id:
            vehicle_stage = self.env['vehicle.service.state']
            vehicle_service_stage = max(vehicle_stage.search([
                ('in_progress', '=', True)
            ]).mapped('sequence'))
            new_stage = vehicle_stage.browse(vals['stage_id'])
            if new_stage.sequence and \
                    new_stage.sequence > vehicle_service_stage:
                if not self.resolution and 'resolution' not in vals:
                    raise ValidationError(_(
                        'You must provide a Resolution on this Service'
                        ' Request before moving it to this Stage.'))
        if vals.get('vehicle_id', False):
            vehicle_id = self.env['fleet.vehicle'].browse(vals['vehicle_id'])
            vals.update(vehicle_id._prepare_vehicle_details())
        res = super(VehicleServices, self).write(vals)
        if 'sr_template_id' in vals:
            self.update_for_sr_template()
        return res

    def create_fleet_repair_lines(self):
        """

        :return:
        """
        if not self.x_location or not self.sr_template_id.operations:
            return
        wh = self.x_location.get_warehouse()
        for operation in self.sr_template_id.operations:
            if operation.type in ['add']:
                operation.copy(default={
                    'location_id': wh.add_source_location.id,
                    'location_dest_id': wh.add_destination_location.id,
                    'service_request_template_id': False,
                    'service_request_id': self.id,
                })
            elif operation.type in ['remove', 'edit']:
                operation.copy(default={
                    'location_id': wh.remove_source_location.id,
                    'location_dest_id': wh.remove_destination_location.id,
                    'service_request_template_id': False,
                    'service_request_id': self.id,
                })

    def create_included_services(self):
        """

        :return:
        """
        vehicle_cost = self.env['fleet.vehicle.cost']
        templ_incl_srv = self.sr_template_id.included_services_ids.read()
        for x in templ_incl_srv:
            x.update({
                'vehicle_services_id': self.id,
                'services_request_template_id': False,
            })
            vehicle_cost.create(vehicle_cost._convert_to_write(x))

    def create_template_images(self):
        """

        :return:
        """
        templ_images = self.sr_template_id.images_ids.ids
        self.images_ids = [(4, x) for x in templ_images]

    @api.model
    def create_services_from_discrepancy(self, vh_discr):
        """

        :param vh_discr:
        :return:
        """
        vehicle_services_rec = self.create({
            'vehicle_discrepancy_id': vh_discr.id,
            'vehicle_id': vh_discr.vehicle_id.id,
            'vehicle_number': vh_discr.vehicle_number,
            'title': vh_discr.title,
            'x_location': vh_discr.x_location and
                          vh_discr.x_location.id or False,
            'observed_date': vh_discr.observed_date,
            'x_flight_hours': vh_discr.x_flight_hours,
            'discrepancy_type_id': vh_discr.discrepancy_type_id and
                                   vh_discr.discrepancy_type_id.id or False,
            'description': vh_discr.description,
            'images_ids': vh_discr.images_ids and [
                (6, 0, vh_discr.images_ids.ids)] or False,
            'x_availability': vh_discr.x_availability.id or '',
            'priority': vh_discr.priority,
            'critical_selection': vh_discr.critical_selection,
            'x_serial_no': vh_discr.x_serial_no,
            'x_hw_config': vh_discr.x_hw_config
        })
        vehicle_services_rec._update_stage_id_priority()
        return vehicle_services_rec

    def _compute_fleet_repair_count(self):
        """
        count all vehicle services related to this vehicle discrepancy.
        :return: None
        """
        for res in self:
            res.fleet_repair_count = len(self.env['fleet.repair.service'].search(
                [('service_id', '=', res.id)]).mapped('repair_id'))

    def action_to_open_repairs(self):
        """
        This opens the xml view specified in xml_id for the current vehicle.
        :return:
        """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        vehicle_services = self.env['fleet.repair.service'].search([
            ('service_id', '=', self.id)
        ])
        if xml_id and vehicle_services:
            domain = [
                ('id', 'in', vehicle_services.repair_id.ids)
            ]
            return return_action_to_open(self, xml_id, domain)
        return False

    @api.onchange('sr_template_id')
    def _onchange_sr_template_id(self):
        """Onchange: SR Template.

        Set values from the SR Template and set to the SR. Like,
            - Title
            - Priority
            - Service Type
            - Service Tags
            - Critical Status
            - Description

        Only if SR Template is available on SR.

        :return: None
        """
        if self.sr_template_id:
            self.title = self.sr_template_id.title
            self.priority = self.sr_template_id.priority
            self.type_id = self.sr_template_id.type_id.id
            self.tag_ids = self.sr_template_id.tag_ids.ids
            self.critical_selection = self.sr_template_id.critical_selection
            self.description = self.sr_template_id.description

    def create_multi_vehicle_sr(self, vehicles):
        """Create Multi Vehicle SR.

        Copy the current SR with default value of vehicle and also set some
        value by calling the onchange of vehicle and SR Template.

        :return: Boolean
        """
        for vehicle in vehicles:
            new_service = self.copy(default={'vehicle_id': vehicle.id})
            new_service.onchange_vehicle_id()
            new_service._update_stage_id_priority()
            new_service._onchange_sr_template_id()
        return True
