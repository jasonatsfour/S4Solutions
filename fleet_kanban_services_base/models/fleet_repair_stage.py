# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import api, fields, models


class FleetRepairStage(models.Model):
    """Fleet Repair Stages

    """
    _name = 'fleet.repair.stage'
    _description = 'Fleet Repair Stage'
    _order = "sequence, id"
    _fold_name = 'folded'

    @api.model
    def _get_sequence(self):
        """Generate Sequence

        :return: Number
        """
        others = self.search([
            ('sequence', '<>', False)
        ], order='sequence desc', limit=1)
        if others:
            return (others[0].sequence or 0) + 1
        return 1

    name = fields.Char('Name', copy=False, required=True)
    sequence = fields.Integer('Sequence', default=_get_sequence)
    is_draft = fields.Boolean(string="Is Draft?")
    folded = fields.Boolean('Folded in kanban view')
    final_stage = fields.Boolean(
        string='Final Stage',
        help='Once the changes are applied, the Repair'
             ' will be moved to this stage.')
    in_progress = fields.Boolean()
    type_id = fields.Many2one('fleet.repair.type', string="")
    approval_roles = fields.Char(
        'Approval Roles', compute='_compute_approvals', store=True)
    is_blocking = fields.Boolean(
        'Blocking Stage', compute='_compute_is_blocking', store=True)
    approval_template_ids = fields.One2many(
        'fleet.repair.approval.template', 'stage_id', 'Approvals')
    allow_apply_change = fields.Boolean(
        string='Allow to apply changes',
        help='Allow to apply changes from this stage.')
    in_work = fields.Boolean(string="In Work")
    moc = fields.Boolean(string="MOC")

    @api.depends('approval_template_ids.name')
    def _compute_approvals(self):
        """

        :return:
        """
        self.approval_roles = ', '.join(
            self.approval_template_ids.mapped('name'))

    @api.depends('approval_template_ids.approval_type')
    def _compute_is_blocking(self):
        """

        :return:
        """
        self.is_blocking = any(
            template.approval_type == 'mandatory'
            for template in self.approval_template_ids)
