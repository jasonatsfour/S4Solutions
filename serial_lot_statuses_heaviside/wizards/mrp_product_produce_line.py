# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC
# See LICENSE file for full copyright & licensing details.

from odoo import models, fields


class MrpProductProduceLine(models.TransientModel):
    """

    """
    _inherit = 'mrp.product.produce.line'

    lot_id = fields.Many2one(
        'stock.production.lot', 'Lot/Serial Number',
        check_company=True,
        domain="[('product_id', '=', product_id),"
               "('is_none_production', '=', False),"
               "('stock_production_lot_status_id.name', '!=', 'Installed'),"
               "'|', ('company_id', '=', False),"
               "('company_id', '=', company_id)]")
