# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class StockQuant(models.Model):
    """

    """
    _inherit = 'stock.quant'

    installed_lot = fields.Boolean(string="Installed Lot")
    partial_serialization_id = fields.Many2one(
        related="product_id.partial_serialization_id", store=True)
    partial_serialization_type = fields.Selection(
        related="product_id.partial_serialization_id.traceability_type",
        string="Product tracking", readonly=True, store=True)

    @api.onchange('location_id', 'product_id', 'lot_id', 'package_id',
                  'owner_id', 'partial_serialization_id',
                  'partial_serialization_type')
    def _onchange_location_or_product_id(self):
        """Onchange: Location or Product

        Change of LOT condition and add Partial Serialization Condition.

        :return: None
        """
        vals = {}
        # Once the new line is complete, fetch the new theoretical values.
        if self.product_id and self.location_id:
            # Sanity check if a lot has been set.
            if self.lot_id:
                if (self.tracking == 'none' and
                    not self.partial_serialization_id) or \
                        self.product_id != self.lot_id.product_id:
                    vals['lot_id'] = None

            quants = self._gather(self.product_id, self.location_id,
                                  lot_id=self.lot_id, owner_id=self.owner_id,
                                  package_id=self.package_id, strict=True)
            reserved_quantity = sum(quants.mapped('reserved_quantity'))
            quantity = sum(quants.mapped('quantity'))

            vals['reserved_quantity'] = reserved_quantity
            # Update `quantity` only if the user
            # manually updated `inventory_quantity`.
            if float_compare(
                    self.quantity, self.inventory_quantity,
                    precision_rounding=self.product_uom_id.rounding) == 0:
                vals['quantity'] = quantity
            # Special case: directly set the quantity
            # to one for serial numbers,
            # it'll trigger `inventory_quantity` compute.
            if self.lot_id and (
                    self.tracking == 'serial' or
                    self.partial_serialization_type == 'serial'):
                vals['quantity'] = 1
        if vals:
            self.update(vals)

    def _set_inventory_quantity(self):
        """
        Override this method to change Location and Name in Stock move
        once we update qty from Update Installed Lots screen
        :return:
        """
        for quant in self:
            if quant.installed_lot:
                # Get the quantity to create a move for.
                rounding = quant.product_id.uom_id.rounding
                diff = float_round(quant.inventory_quantity - quant.quantity,
                                   precision_rounding=rounding)
                diff_float_compared = float_compare(
                    diff, 0, precision_rounding=rounding)
                # Search Supplier Location for the company
                # and set in Product Moves
                supplier_location = self.env['stock.location'].search([
                    ('usage', '=', 'supplier'),
                    ('company_id', 'in', [False, quant.company_id.id])
                ], limit=1)
                if not supplier_location:
                    supplier_location = quant.product_id.with_context(
                        force_company=quant.company_id.id or
                        self.env.company.id
                    ).property_stock_inventory
                if diff_float_compared == 0:
                    continue
                elif diff_float_compared > 0:
                    move_vals = quant._get_inventory_move_values(
                        diff, supplier_location, quant.location_id)
                else:
                    move_vals = quant._get_inventory_move_values(
                        -diff, quant.location_id, supplier_location, out=True)
                # Change Product Move name to identify
                # Supplier Installation Record
                move_vals['name'] = "Supplier Installation Record"
                move = quant.env['stock.move'].with_context(
                    inventory_mode=False).create(move_vals)
                move._action_done()
                return True
        return super(StockQuant, self)._set_inventory_quantity()

    @api.model
    def _update_reserved_quantity(
            self, product_id, location_id, quantity, lot_id=None,
            package_id=None, owner_id=None, strict=False):
        """

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
                    'It is not possible to unreserve more products of %s '
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
