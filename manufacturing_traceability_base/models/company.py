# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    """Res Company

    Fields:
    supplier_location_id: Default Inventory Location.
    """
    _inherit = 'res.company'

    supplier_location_id = fields.Many2one(
        'stock.location', string="Location",
        help="Set default location for inventory.")

    advance_quality_failure = fields.Boolean(string="Advance Quality Failure",
                                             help="Check it to get advance failure popup.")

