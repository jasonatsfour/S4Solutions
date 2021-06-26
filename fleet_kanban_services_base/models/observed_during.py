# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class ObservedDuring(models.Model):
    """

    """
    _name = 'observed.during'
    _description = 'Observed During'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)
