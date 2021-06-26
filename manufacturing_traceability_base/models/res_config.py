# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """

    """
    _inherit = 'res.config.settings'

    supplier_location_id = fields.Many2one(
        related='company_id.supplier_location_id',
        string="Default Location", readonly=False)
