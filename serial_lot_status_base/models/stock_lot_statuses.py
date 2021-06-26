# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class StockLotsStatus(models.Model):
    """Stock Lot Status.

    Fields:
    name
    key: Must be in lower case
    """
    _name = 'stock.production.lot.status'
    _description = 'Stock Production Lot Status'

    name = fields.Char(string="Name")
    key = fields.Char(string="Key")
