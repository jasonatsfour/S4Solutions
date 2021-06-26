# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class QualityCheck(models.Model):
    """Inherited: Quality Check

    Fields:
    component_id: Redefined to change the string.
    lot_id: Redefine to change the domain.
    """
    _inherit = "quality.check"

    component_id = fields.Many2one(
        'product.product', string='Product To Register', check_company=True)
    lot_id = fields.Many2one(
        'stock.production.lot', string="Lot",
        domain="('company_id', 'in', [False, company_id])")
