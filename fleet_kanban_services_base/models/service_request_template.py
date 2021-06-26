# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api


class ServiceRequestTemplate(models.Model):
    """

    """
    _name = 'service.request.template'
    _description = 'Service Request Template'
    _order = "id"
    _rec_name = 'name'

    name = fields.Char(string='Service Request Template', required=True)
    title = fields.Char(string='Title', required=True)
    type_id = fields.Many2one(
        'vehicle.service.type',
        string='Service Type', track_visibility='onchange')
    tag_ids = fields.Many2many('vehicle.service.tag', string='Service Tags')
    included_services_ids = fields.One2many(
        'included.services', 'services_request_template_id', string='Task')
    images_ids = fields.Many2many('ir.attachment', string='Image')
    description = fields.Text(string='Description', limit=500)
    priority = fields.Selection([
        ('non-critical', 'Non-Grounded'),
        ('critical', 'Grounded')
    ], string='Grounding Status', track_visibility='onchange')
    critical_selection = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], track_visibility='onchange')
    operations = fields.One2many(
        'fleet.repair.line', 'service_request_template_id',
        string='Parts', copy=True)

    @api.onchange('priority')
    def _onchange_priority(self):
        """

        :return: None
        """
        for record in self:
            if record.priority == 'non-critical':
                record.critical_selection = 'no'
            else:
                record.critical_selection = 'yes'
