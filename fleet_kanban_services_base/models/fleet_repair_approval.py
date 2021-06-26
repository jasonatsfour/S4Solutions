# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import api, fields, models


class FleetRepairApproval(models.Model):
    """

    """
    _name = "fleet.repair.approval"
    _description = 'Repair Approval'

    repair_id = fields.Many2one('fleet.repair', string='Repair',
                                ondelete='cascade', required=True)
    approval_template_id = fields.Many2one(
        'fleet.repair.approval.template', string='Template',
        ondelete='cascade', required=True)
    name = fields.Char(
        string='Role', related='approval_template_id.name',
        store=True, readonly=False)
    user_id = fields.Many2one('res.users', string='Approved by')
    required_user_ids = fields.Many2many(
        'res.users', string='Requested Users',
        related='approval_template_id.user_ids', readonly=False)
    template_stage_id = fields.Many2one(
        'fleet.repair.stage', string='Approval Stage',
        related='approval_template_id.stage_id', store=True, readonly=False)
    repair_stage_id = fields.Many2one(
        'fleet.repair.stage', string='Repair Stage',
        related='repair_id.stage_id', store=True, readonly=False)
    status = fields.Selection([
        ('none', 'Not Yet'),
        ('comment', 'Commented'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='none', required=True)
    is_approved = fields.Boolean(compute='_compute_is_approved', store=True)
    is_rejected = fields.Boolean(compute='_compute_is_rejected', store=True)

    @api.depends('status', 'approval_template_id.approval_type')
    def _compute_is_approved(self):
        """

        :return:
        """
        if self.approval_template_id.approval_type == 'mandatory':
            self.is_approved = self.status == 'approved'
        else:
            self.is_approved = True

    @api.depends('status', 'approval_template_id.approval_type')
    def _compute_is_rejected(self):
        """

        :return:
        """
        if self.approval_template_id.approval_type == 'mandatory':
            self.is_rejected = self.status == 'rejected'
        else:
            self.is_rejected = False
