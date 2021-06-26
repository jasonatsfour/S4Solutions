# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api, _


class VehicleDiscrepancy(models.Model):
    """

    """
    _name = 'vehicle.discrepancy'
    _description = 'Vehicle Discrepancy'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Vehicle Discrepancy', copy=False,
                       default=lambda self: _('New'), readonly=True)
    vehicle_number = fields.Char(string='Vehicle Number')
    title = fields.Char(string='Title')
    vehicle_id = fields.Many2one('fleet.vehicle', track_visibility='onchange')
    x_availability = fields.Many2one('fleet.vehicle.available',
                                     string='Availability')
    x_location = fields.Many2one('stock.location', string='Location')
    x_flight_hours = fields.Float(string='Flights Hours',
                                  track_visibility='onchange')
    discrepancy_type_id = fields.Many2one(
        'vehicle.discrepancy.type', string='Discrepancy Type',
        track_visibility='onchange')
    observed_date = fields.Datetime(string='Observed Date', copy=False)
    description = fields.Text(string='Description', limit=500)
    images_ids = fields.Many2many('ir.attachment', string='Image')
    priority = fields.Selection([
        ('non-critical', 'Non-Grounded'),
        ('critical', 'Grounded')
    ], string='Grounding Status', track_visibility='onchange')
    vehicle_services_count = fields.Integer(
        compute='_compute_vehicle_services_count',
        string='# of Vehicle Services')
    is_grounded = fields.Boolean(string='Is Grounded?', default=False)
    critical_selection = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Critical', track_visibility='onchange')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.user.company_id
    )
    observed_during = fields.Many2one('observed.during',
                                      string='Observed During')
    hw_failure_mode_ids = fields.Many2many('hw.failure.mode',
                                           string='HW Failure Mode')
    x_hw_config = fields.Char(string='HW Version',
                              track_visibility='onchange')
    x_serial_no = fields.Char(string='Serial #', track_visibility='onchange')

    @api.model
    def create(self, vals):
        """
        Override Create Method to add vehicle discrepancy sequence.
        :param vals:
        :return:
        """
        vehicle_service = self.env['vehicle.services']
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'vehicle.discrepancy') or _('New')
        if vals.get('vehicle_id', False):
            vehicle_id = self.env['fleet.vehicle'].browse(vals['vehicle_id'])
            vals.update(vehicle_id._prepare_vehicle_details())
        res = super(VehicleDiscrepancy, self).create(vals)
        vehicle_service.create_services_from_discrepancy(res)
        return res

    def write(self, vals):
        """

        :param vals:
        :return:
        """
        if vals.get('vehicle_id', False):
            vehicle_id = self.env['fleet.vehicle'].browse(vals['vehicle_id'])
            vals.update(vehicle_id._prepare_vehicle_details())
        return super(VehicleDiscrepancy, self).write(vals)

    @api.onchange('vehicle_id')
    def onchange_vehicle_id(self):
        """

        :return: None
        """
        for discrepancy in self:
            vehicle = discrepancy.vehicle_id
            discrepancy.vehicle_number = vehicle.license_plate
            discrepancy.x_location = vehicle.x_location and \
                                     vehicle.x_location.id or False
            discrepancy.x_availability = vehicle.x_availability.id
            discrepancy.x_flight_hours = vehicle.x_flight_hours
            discrepancy.x_serial_no = vehicle.x_serial_no
            discrepancy.x_hw_config = vehicle.x_hw_config

    def _compute_vehicle_services_count(self):
        """
        Count all vehicle services related to this vehicle discrepancy.
        :return: None
        """
        sr = self.env['vehicle.services']
        for rec in self:
            rec.vehicle_services_count = sr.search_count([
                ('vehicle_discrepancy_id', '=', rec.id)
            ])
