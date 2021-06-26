# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class VehicleRecurringServiceHistory(models.Model):
    """Recurring History Log

    """
    _name = 'vehicle.recurring.service.history'
    _description = 'Vehicle Recurring Service History'
    _order = 'create_date DESC, id DESC'
    _rec_name = 'vehicle_id'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    vehicle_service_id = fields.Many2one('vehicle.services',
                                         ondelete='cascade', string='Service')
    recurring_service_plan_id = fields.Many2one(
        'recurring.service.plan', ondelete='cascade',
        string='Recurring Service Plan')
    interval_threshold = fields.Integer(string='Interval Threshold')
    interval_hours = fields.Integer(string='Interval Hours')
    services_request_template_id = fields.Many2one(
        'service.request.template', string='Service Request Template',
        track_visibility='onchange')
    last_generated_hours = fields.Float(string='Last Generated At Hours')
    hours_till_next_generation = fields.Float(
        string='Hours till next generation with threshold')
    hours_till_next_generation_without_threshold = fields.Float(
        string='Hours till next generation without threshold')
