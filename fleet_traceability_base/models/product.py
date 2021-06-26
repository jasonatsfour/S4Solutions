# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models, api


class ProductProduct(models.Model):
    """

    """
    _inherit = 'product.product'

    @api.model
    def _search(self, args, offset=0, limit=None, order=None,
                count=False, access_rights_uid=None):
        """
        This method is used to get the list of product of respected lot number
        whose installed location as parent_lot_id in repair order.
        :param args:
        :param offset:
        :param limit:
        :param order:
        :param count:
        :param access_rights_uid:
        :return: Recordset
        """
        if self._context.get('type') in ['remove', 'edit'] and \
                self._context.get('lot_id'):
            lot_id = self.env['stock.production.lot'].browse(
                self._context['lot_id'])
            children = lot_id._get_root_children()
            args.append((('id', 'in', children.mapped('product_id').ids)))
        return super(ProductProduct, self)._search(
            args, offset, limit, order, count=count,
            access_rights_uid=access_rights_uid)
