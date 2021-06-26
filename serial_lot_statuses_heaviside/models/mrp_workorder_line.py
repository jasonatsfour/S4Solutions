# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class MrpAbstractWorkorderLine(models.AbstractModel):
    """
    To set up Not for Flight Boolean
    """

    _inherit = "mrp.abstract.workorder.line"

    # Added is_none_production in exist field domain
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number',
                             check_company=True,
                             domain="[('is_none_production', '=', False), "
                                    "('product_id', '=', product_id), "
                                    "'|', ('company_id', '=', False), "
                                    "('company_id', '=', parent.company_id)]")
