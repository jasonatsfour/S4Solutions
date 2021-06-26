# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class FleetRepairLine(models.Model):
    """

    """
    _inherit = 'fleet.repair.line'

    type = fields.Selection(selection_add=[('edit', 'Replace')])
    replacement_lot_id = fields.Many2one(
        'stock.production.lot', 'Replacement Lot/Serial')
    parent_lot_id = fields.Many2one(related='repair_id.lot_id',
                                    string="Parent Lot/Serial")
    origin_part_of_id = fields.Many2one('stock.production.lot',
                                        string='Origin Lot/Serial')

    @api.onchange('type')
    def onchange_type(self):
        """

        :return:
        """
        if self.product_id:
            self.name = self.product_id = False
            self.replacement_lot_id = self.lot_id = False
            return

        wh = False
        if self.repair_id.x_location:
            wh = self.repair_id.x_location.get_warehouse()
        elif self.service_request_id.x_location:
            wh = self.service_request_id.x_location.get_warehouse()

        if self.type == 'add' and wh:
            self.location_id = wh.add_source_location.id
            self.location_dest_id = wh.add_destination_location.id
        elif self.type in ['remove', 'edit'] and wh:
            self.location_id = wh.remove_source_location.id
            self.location_dest_id = wh.remove_destination_location.id

    def operation_edit_type(self):
        """

        Method to create 2 move lines and operation for edit type operations.

        :return: None
        """
        for line in self.filtered(lambda l: l.replacement_lot_id):
            line._add_replacement_lines(line.lot_id, 'remove')
            line._add_replacement_lines(line.replacement_lot_id)
            child_lot = line.lot_id._get_root_children_after_map_parent(
                line.origin_part_of_id)
            if child_lot:
                child_lot.adopt_children(line.lot_id, line.replacement_lot_id)
            line.unlink()

    def _add_replacement_lines(self, lot, line_type='add'):
        """

        :param lot:
        :param line_type:
        :return: None
        """
        new_line = self.new({
            'type': line_type,
            'product_id': lot.product_id.id,
            'lot_id': lot.id,
            'repair_id': self.repair_id.id,
            'price_unit': 0.0,
            'product_uom': 1,
            'product_uom_qty': 1,
            'origin_part_of_id': self.origin_part_of_id.id,
        })
        new_line.refurbish()
        new_line = new_line._convert_to_write({
            name: new_line[name] for name in new_line._cache
        })
        new_line = self.create(new_line)
        if new_line.fleet_use:
            new_line.action_make_done()

    def _check_before_done(self):
        """

        :return: None or Error
        :raise: Validation Error
        """
        if self.fleet_use and not self.lot_id:
            raise ValidationError(_(
                "A Lot/Serial number must be provided for %s prior to"
                " marking it Done") % self.product_id.display_name)
        if self.type == 'edit' and not self.replacement_lot_id:
            raise ValidationError(
                _("A Replacement Lot/Serial number must be provided for "
                  "this record prior to marking it Done"))

    def check_for_edit_operations(self):
        """

        :return: None
        """
        edit_lines = self.filtered(
            lambda l: l.type == 'edit'
        )
        edit_lines.operation_edit_type()

    def action_make_done(self):
        """

        :return: None
        """
        super(FleetRepairLine, self).action_make_done()
        self.check_for_edit_operations()

    def prepare_line_as_maintained_history(self, lot_id, lot_version):
        """

        :param lot_id:
        :param lot_version:
        :return:
        """
        return {
            'lot_type': self.type,
            'repair_order_line_id': self.id,
            'as_maintained_child_lot_id': self.lot_id.id,
            'product_id': self.product_id.id,
            'price_unit': self.price_unit,
            'product_uom_qty': self.product_uom_qty,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'as_maintained_parent_lot_id': lot_id.id,
            'parent_lot_version': lot_version,
            'origin_part_of_id': self.origin_part_of_id.id or lot_id.id,
        }

    def create_fleet_repair_as_maintained_history(self, lot_id, lot_version):
        """

        :param lot_id:
        :param lot_version:
        :return: None
        """
        as_maintained = self.env['as_maintained.history']
        as_maintained_history_id = as_maintained.create(
            self.prepare_line_as_maintained_history(lot_id, lot_version)
        )
        lot_id._update_as_maintained_history_version(
            lot_version, as_maintained_history_id)

    def refurbish(self):
        """

        :return: None
        """
        self.onchange_operation_type()
        self.onchange_product_id()
        self._compute_fleet_in_use()
