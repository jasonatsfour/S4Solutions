# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api


class VehicleServiceState(models.Model):
    """

    """
    _name = 'vehicle.service.state'
    _description = 'Service Stage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "sequence, id"
    _fold_name = 'folded'

    @api.model
    def _get_sequence(self):
        """

        :return:
        """
        others = self.search([
            ('sequence', '<>', False)
        ], order='sequence desc', limit=1)
        if others:
            return (others[0].sequence or 0) + 1
        return 1

    name = fields.Char(string='Name')
    sequence = fields.Integer(string='Sequence', default=_get_sequence)
    is_draft = fields.Boolean(string='Is Draft?')
    folded = fields.Boolean(string='Folded in kanban view')
    in_progress = fields.Boolean(string='In Progress?')
    final_stage = fields.Boolean(
        string='Final Stage',
        help='Once the changes are applied, '
             'the ECOs will be moved to this stage.')
