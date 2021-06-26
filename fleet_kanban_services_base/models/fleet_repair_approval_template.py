# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class FleetRepairApprovalTemplate(models.Model):
    """

    """
    _name = "fleet.repair.approval.template"
    _order = "sequence"
    _description = 'Repair Approval Template'

    name = fields.Char(string='Role', required=True)
    sequence = fields.Integer(string='Sequence')
    approval_type = fields.Selection([
        ('optional', 'Approves, but the approval is optional'),
        ('mandatory', 'Is required to approve'),
        ('comment', 'Comments only')
    ], string='Approval Type', default='mandatory', required=True)
    user_ids = fields.Many2many('res.users', string='Users', required=True)
    stage_id = fields.Many2one(
        'fleet.repair.stage', string='Stage', required=True)
