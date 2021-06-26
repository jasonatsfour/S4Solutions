# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class StockLocation(models.Model):
    """

    """
    _inherit = 'stock.location'

    asset_location = fields.Boolean(string='Asset Location', default=False)
