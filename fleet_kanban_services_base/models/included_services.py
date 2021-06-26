# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api


class IncludedServices(models.Model):
    """

    """
    _name = 'included.services'
    _description = 'Included Services'

    cost_subtype_id = fields.Many2one(
        'fleet.service.type', string='Type',
        help='Cost type purchased with this cost')
    amount = fields.Float(string='Total Price')
    services_request_template_id = fields.Many2one(
        'service.request.template', string="Service Request Template")
    x_completed_by = fields.Many2one('res.users', string='Completed By')
