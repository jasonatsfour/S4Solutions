# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class StockProductionLot(models.Model):
    """Inherited: Lot/Serial Number.

    Fields:
    company_id: Override to set default company from current user

    Methods:
    get_root_lot: Fetch parent or root of all parent lot
    _get_root_children: Fetch all children of children
    _get_root_children_after_map_parent: Fetch only current lot children who
    belongs to same root parent
    adopt_children: Change parent of children

    """
    _inherit = 'stock.production.lot'

    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.user.company_id)

    def get_root_lot(self):
        """Get Root Lot

        To get the root Serial/Lot of current Serial/Lot.

        If there is not installed location then it will return itself, it means
        you will always get recordset of Serial/Lot object.

        :return: Recordset - Root Serial/Lot
        """
        if not self.lot_ids:
            return self
        return self.lot_ids[0].get_root_lot()

    def _get_root_children(self):
        """Find Children

        :return: Recordset
        """
        child_lot = self
        lots = self.search([
            ('lot_ids', 'in', self.ids)
        ])
        if lots:
            child_lot |= lots._get_root_children()
        return child_lot

    def _get_root_children_after_map_parent(self, parent_lot):
        """Find Children

        :return: Recordset
        """
        lots = self.search([
            ('lot_ids', 'in', self.ids)
        ])
        if not lots:
            return
        child_lots = self.env['stock.production.lot']
        parent_lot = parent_lot.get_root_lot()
        for lot in lots:
            if lot.get_root_lot() == parent_lot:
                child_lots |= lot
        return child_lots

    def adopt_children(self, old_parent_lot, new_parent_lot):
        """Adopt Children from Lot/Serial.

        While replace any lot it children must be follow the new one.
        Replace the Component Parent Lot/Serial.

        :param old_parent_lot: Target Lot/Serial
        :param new_parent_lot: Replacement Lot/Serial
        :return: Boolean
        """
        self.write({
            'lot_ids': [(3, old_parent_lot.id), (4, new_parent_lot.id)]
        })
        return True
