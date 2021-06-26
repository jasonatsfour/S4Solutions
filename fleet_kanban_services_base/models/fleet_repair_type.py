# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class FleetRepairType(models.Model):
    """

    """
    _name = 'fleet.repair.type'
    _description = 'Fleet Repair Type'
    _inherit = ['mail.alias.mixin', 'mail.thread']

    name = fields.Char(string='Name', copy=False, required=True)
    sequence = fields.Integer(string='Sequence')
    alias_id = fields.Many2one(
        'mail.alias', string='Alias', ondelete='restrict', required=True)
    nb_repairs = fields.Integer(string='Repair', compute='_compute_nb')
    nb_approvals = fields.Integer(
        string='Waiting Approvals', compute='_compute_nb')
    nb_approvals_my = fields.Integer(
        string='Waiting my Approvals', compute='_compute_nb')
    nb_validation = fields.Integer('To Apply', compute='_compute_nb')
    stage_ids = fields.One2many(
        'fleet.repair.stage', 'type_id', string='Stages')

    def get_alias_model_name(self, vals):
        """

        :param vals:
        :return:
        """
        return vals.get('alias_model', 'fleet.repair')

    def get_alias_values(self):
        """

        :return:
        """
        values = super(FleetRepairType, self).get_alias_values()
        values['alias_defaults'] = {'type_id': self.id}
        return values
