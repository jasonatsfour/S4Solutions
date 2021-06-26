# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, _
from odoo.exceptions import UserError


class HwFailureMode(models.Model):
    """HW Failure Mode

    Fields:
    name
    note
    active

    ORM:
    unlink
    """
    _name = 'hw.failure.mode'
    _description = 'HW Failure Mode'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)
    note = fields.Text(string="Description")
    active = fields.Boolean(default=True, string="Active")

    def unlink(self):
        """ORM: Delete.

        Allow users to archive HW failure modes and prevent users from
        deleting HW failure modes which have been used on a discrepancy.

        Raise the list of HW Failure within warning.

        :return: Super call
        :raise: User Error
        """
        used = set(self.env['vehicle.discrepancy'].search([]).mapped(
            'hw_failure_mode_ids').ids)
        intersection = self.filtered(
            lambda hw: hw.id in list(used.intersection(set(self.ids)))
        )
        if intersection:
            raise UserError(_(
                "You can not delete few of selected. "
                "Those are used in Discrepancy:"
            ) + "\n%s" % '\n'.join(
                intersection.mapped('name')
            ) if len(intersection) > 1 else _(
                "You can not delete, %s is used in Discrepancy"
            ) % intersection.name
                            )
        return super(HwFailureMode, self).unlink(self)
