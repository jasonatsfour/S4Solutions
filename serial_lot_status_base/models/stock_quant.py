# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero


class StockQuant(models.Model):
    """Inherited: Stock Quants.

    Methods:
    _update_reserved_quantity

    ORM:
    create
    write
    """
    _inherit = 'stock.quant'

    def write(self, vals):
        """ORM: Write

        Override this method to manage Inventory Status.

        :param vals: Received values in dictionary format
        :return: None
        """
        product_ref = self.env['product.product']
        production_lot = self.env['stock.production.lot']
        for rec in self:
            location_id = vals.get('location_id', False) or (
                    rec.location_id and rec.location_id.id) or False
            lot_id = vals.get('lot_id', False) or (
                    rec.lot_id and rec.lot_id.id) or False
            quantity = vals.get('quantity', False) or rec.quantity or 0
            product_id = vals.get('product_id', rec.product_id)
            if isinstance(product_id, int):
                product_id = product_ref.browse(product_id)
            # Manage Serial Status for Serialized Product
            if location_id and lot_id and quantity > 0 and product_id and \
                    product_id.is_serial_product():
                lot_id = production_lot.browse(lot_id)
                lot_id.calculate_lot_status(location_id)
        return super(StockQuant, self).write(vals)

    @api.model
    def create(self, vals):
        """ORM: Create
        Override this method to manage Inventory Status.
        :param vals: Received values in dictionary format
        :return: Recordset of Stock Quant
        """
        active_model = self._context.get('active_model')
        active_id = self._context.get('active_id')
        product_lot = self.env['stock.production.lot']
        installed_lot = product_lot.browse(active_id)
        # Add active model for context.
        if active_model == 'stock.production.lot' and \
                vals.get('lot_id') != active_id and installed_lot:
            lot_id = product_lot.browse(vals.get('lot_id'))
            lot_id.write({
                'lot_ids': [(4, installed_lot.id)]
            })
        res = super(StockQuant, self).create(vals)
        # Manage Serial Status for Serialized Product
        if res.location_id and res.lot_id and res.quantity > 0 and \
                res.product_id and res.product_id.is_serial_product():
            res.lot_id.calculate_lot_status(res.location_id.id)
        return res

    @api.model
    def _update_reserved_quantity(
            self, product_id, location_id, quantity, lot_id=None,
            package_id=None, owner_id=None, strict=False):
        """Override: Update Reserved Quant

        Added domain to filter to reserve quant, those are not used for flight.

        :param product_id:
        :param location_id:
        :param quantity:
        :param lot_id:
        :param package_id:
        :param owner_id:
        :param strict:
        :return: Recordset for Reserved Quants or Raise Error
        :raise: User Error
        """
        self = self.sudo()
        rounding = product_id.uom_id.rounding
        quants = self._gather(
            product_id, location_id, lot_id=lot_id, package_id=package_id,
            owner_id=owner_id, strict=strict)
        reserved_quants = []

        if float_compare(quantity, 0, precision_rounding=rounding) > 0:
            # if we want to reserve
            available_quantity = self._get_available_quantity(
                product_id, location_id, lot_id=lot_id, package_id=package_id,
                owner_id=owner_id, strict=strict)
            if float_compare(quantity, available_quantity,
                             precision_rounding=rounding) > 0:
                raise UserError(_(
                    'It is not possible to reserve more products of %s '
                    'than you have in stock.') % product_id.display_name)
        elif float_compare(quantity, 0, precision_rounding=rounding) < 0:
            # if we want to unreserve
            available_quantity = sum(quants.mapped('reserved_quantity'))
            if float_compare(abs(quantity), available_quantity,
                             precision_rounding=rounding) > 0:
                raise UserError(_(
                    'It is not possible to unreserved more products of %s '
                    'than you have in stock.') % product_id.display_name)
        else:
            return reserved_quants

        for quant in quants.filtered(
                lambda q: not q.lot_id.is_none_production):
            if float_compare(quantity, 0, precision_rounding=rounding) > 0:
                max_quantity_on_quant = quant.quantity - \
                                        quant.reserved_quantity
                if float_compare(max_quantity_on_quant, 0,
                                 precision_rounding=rounding) <= 0:
                    continue
                max_quantity_on_quant = min(max_quantity_on_quant, quantity)
                quant.reserved_quantity += max_quantity_on_quant
                reserved_quants.append((quant, max_quantity_on_quant))
                quantity -= max_quantity_on_quant
                available_quantity -= max_quantity_on_quant
            else:
                max_quantity_on_quant = min(quant.reserved_quantity,
                                            abs(quantity))
                quant.reserved_quantity -= max_quantity_on_quant
                reserved_quants.append((quant, -max_quantity_on_quant))
                quantity += max_quantity_on_quant
                available_quantity += max_quantity_on_quant

            if float_is_zero(
                    quantity, precision_rounding=rounding
            ) or float_is_zero(available_quantity,
                               precision_rounding=rounding):
                break
        return reserved_quants
