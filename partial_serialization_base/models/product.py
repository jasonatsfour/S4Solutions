# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    """Product Template

    To manage partial serialization.

    Fields:
    partial_serialization_id: To manage partial serial/lot.

    Methods:
    is_serialization_product
    is_partial_serialization_product
    is_product_fleet_use
    is_product_manufacturing_use
    is_serial_product
    is_lot_product

    ORM:
    create
    write
    onchange_tracking -> tracking
    """
    _inherit = 'product.template'

    partial_serialization_id = fields.Many2one(
        "vehicle.partial.serialization",
        string="Partial Serialization")

    def is_serialization_product(self):
        """Serialization Product.

        To check that current product traceability is partial serial or
        it doest have any tacking policy.

        :return: Boolean
        """
        return self.partial_serialization_id and self.tracking != 'none'

    def is_partial_serialization_product(self):
        """Partial Serialization Product.

        To check that current product traceability is partial serial and
        it doest have any tacking policy.

        :return: Boolean
        """
        return self.partial_serialization_id and self.tracking == 'none'

    def is_product_fleet_use(self):
        """Product for fleet usage.

        To check that current product traceability is partial serial and
        it doest have any tacking policy and also it must use for Fleet.

        :return: Boolean
        """
        return (
                       self.tracking != 'none' and not
                       self.partial_serialization_id
               ) or (
                       self.partial_serialization_id and
                       self.partial_serialization_id.fleet_use
               )

    def is_product_manufacturing_use(self):
        """Product for MRP usage.

        To check that current product traceability is partial serial and
        it doest have any tacking policy and also it must use for MRP.

        :return: Boolean
        """
        return (
                       self.tracking != 'none' and not
                       self.partial_serialization_id
               ) or (
                       self.partial_serialization_id and
                       self.partial_serialization_id.manufacturing_use
               )

    def is_serial_product(self):
        """Serial Product

        To check current product tacking is serial or not

        :return: Boolean
        """
        return self.partial_serialization_id and \
               self.partial_serialization_id.traceability_type == 'serial' or \
               self.tracking == 'serial'

    def is_lot_product(self):
        """Lot Product

        To check current product tacking is lot or not

        :return: Boolean
        """
        return self.partial_serialization_id and \
               self.partial_serialization_id.traceability_type == 'lot' or \
               self.tracking == 'lot'

    @api.model
    def create(self, vals):
        """ORM: Create.

        To check the current product must not create tracking as
        default Serial/Lot along with Partial Serial.

        :param vals: Received values in dictionary format
        :return: Recordset of Product Template or Raise Error
        :raise: User Error
        """
        if vals.get('partial_serialization_id') and \
                vals.get('tracking') in ['serial', 'lot']:
            raise UserError(_(
                'Cannot set Traceability as By Unique Serial or By Lots.'
            ))
        return super(ProductTemplate, self).create(vals)

    def write(self, vals):
        """ORM: Write.

        To check the current product must not write tracking as
        default Serial/Lot along with Partial Serial.

        :param vals: Received values in dictionary format
        :return: None or Raise Error
        :raise: User Error
        """
        if (vals.get('partial_serialization_id') or
            self.partial_serialization_id
        ) and (vals.get('tracking') in ['serial', 'lot'] or
               self.tracking in ['serial', 'lot']):
            raise UserError(_(
                'Cannot set Traceability as By '
                'Unique Serial Number or By Lots.'
            ))
        return super(ProductTemplate, self).write(vals)

    @api.onchange('tracking')
    def onchange_tracking(self):
        """Change Product Tracking.

        If Product tracking changed none to something
        than partial serial must be reset with False.

        :return: None
        """
        if self.tracking != 'none':
            self.partial_serialization_id = False


class ProductProduct(models.Model):
    """Product Variants

    Methods:
    is_serialization_product
    is_partial_serialization_product
    is_product_fleet_use
    is_product_manufacturing_use
    is_serial_product
    is_lot_product

    ORM:
    onchange_tracking -> tracking
    """
    _inherit = 'product.product'

    def is_serialization_product(self):
        """Serialization Product.

        To check that current product traceability is serial or
        it doest have any tacking policy.

        :return: Boolean
        """
        return self.partial_serialization_id or self.tracking != 'none'

    def is_partial_serialization_product(self):
        """Partial Serialization Product.

        To check that current product traceability is partial serial and
        it doest have any tacking policy.

        :return: Boolean
        """
        return self.partial_serialization_id and self.tracking == 'none'

    def is_product_fleet_use(self):
        """Product for fleet usage.

        To check that current product traceability is partial serial and
        it doest have any tacking policy and also it must use for Fleet.

        :return: Boolean
        """
        return (
                   self.tracking != 'none' and not
                   self.partial_serialization_id
           ) or (
                   self.partial_serialization_id and
                   self.partial_serialization_id.fleet_use
           )

    def is_product_manufacturing_use(self):
        """Product for MRP usage.

        To check that current product traceability is partial serial and
        it doest have any tacking policy and also it must use for MRP.

        :return: Boolean
        """
        return (
                       self.tracking != 'none' and not
                       self.partial_serialization_id
               ) or (
                       self.partial_serialization_id and
                       self.partial_serialization_id.manufacturing_use
               )

    def is_serial_product(self):
        """Serial Product.

        To check current product tacking is serial or not.

        :return: Boolean
        """
        return self.partial_serialization_id and \
            self.partial_serialization_id.traceability_type == 'serial' or \
            self.tracking == 'serial'

    def is_lot_product(self):
        """Lot Product.

        To check current product tacking is lot or not.

        :return: Boolean
        """
        return self.partial_serialization_id and \
            self.partial_serialization_id.traceability_type == 'lot' or \
            self.tracking == 'lot'

    @api.onchange('tracking')
    def onchange_tracking(self):
        """Change Product Tracking.

        If Product tracking changed none to something
        than partial serial must be reset with False.

        :return: None
        """
        if self.tracking != 'none':
            self.partial_serialization_id = False
