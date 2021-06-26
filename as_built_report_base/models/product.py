# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models, api


class ProductProduct(models.Model):
    """Inherited: Product

    ORM:
    _search: for manage context base M2O for repair liens.
    """
    _inherit = "product.product"

    @api.model
    def _search(self, args, offset=0, limit=None, order=None,
                count=False, access_rights_uid=None):
        """ORM: _search

        This method is used to get the list of product of respected lot number
        whose installed location as parent_lot_id in Repair only if operation
        type is removed in context else base method will call as is.

        :param args:
        :param offset:
        :param limit:
        :param order:
        :param count:
        :param access_rights_uid:
        :return: a list of record ids or an integer (if count is True)
        """
        domain = []
        if self._context.get('operation_type') == 'remove' and \
                self._context.get('lot_id'):
            domain += [('lot_ids', 'in', [self._context.get('lot_id')])]
            product_rec = self.env['stock.production.lot'].search(
                domain).mapped('product_id').ids
            args.append(('id', 'in', product_rec))
        return super(ProductProduct, self)._search(
            args, offset, limit, order, count=count,
            access_rights_uid=access_rights_uid)
