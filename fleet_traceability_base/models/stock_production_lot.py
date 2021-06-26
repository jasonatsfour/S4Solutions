# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import api, fields, models, _


class StockProductionLot(models.Model):
    """Inherit: Lot/Serial Number

    """
    _inherit = 'stock.production.lot'

    # override this field to change the string name and add related in it
    ref = fields.Char(
        string='Product Number', related='product_id.default_code',
        track_visibility='onchange',
        help="Product number in case it differs from "
             "the manufacturer's lot/serial number")
    lot_version = fields.Integer(string='Lot Version', default=1,
                                 track_visibility='onchange')
    is_non_traceable = fields.Boolean(string='Is Non-Traceable', default=False,
                                      track_visibility='onchange')
    location_id = fields.Many2one('stock.location', string='Location',
                                  track_visibility='onchange')
    as_maintained_history_ids = fields.One2many(
        'as_maintained.history', 'lot_id', string="As-Maintained Lot History")
    sub_part_history_ids = fields.One2many(
        'as_maintained.history', 'origin_part_of_id',
        string="Sub Part History")

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """ORM: Name Search

        To get the list of lot with respected its type which is selected in
        Operation(Repair Lines - repair.order.line).

        :param name:
        :param args:
        :param operator:
        :param limit:
        :return: Recordset
        """
        domain = []
        lot_status = self.env['stock.production.lot.status']
        # for lot serial number if the type is remove and edit
        if (self._context.get('type') == 'remove' or
            self._context.get('type') == 'edit') and \
                self._context.get('product_id') and \
                self._context.get('parent_lot_id'):
            domain += [
                ('product_id', '=', self._context.get('product_id')),
                ('lot_ids', 'in', [self._context.get('parent_lot_id')])
            ]
        # for lot serial number if the type is add
        elif self._context.get('type') == 'add' and \
                self._context.get('product_id') and \
                self._context.get('parent_lot_id'):
            available_lot_status = lot_status.search([
                ('key', 'in', ['available', 'inventory'])
            ]).ids
            domain += [
                ('id', '!=', self._context.get('parent_lot_id')),
                ('product_id', '=', self._context.get('product_id')),
                ('stock_production_lot_status_id', 'in', available_lot_status),
                ('is_none_production', '=', False),
            ]
        # for replacement lot serial number if the type is edit
        elif self._context.get('edit_type') == 'edit' and \
                self._context.get('parent_lot_id'):
            available_lot_status = lot_status.search([
                ('key', 'in', ['available', 'inventory'])
            ]).ids
            domain += [
                ('id', '!=', self._context.get('parent_lot_id')),
                ('stock_production_lot_status_id', 'in', available_lot_status)
            ]
        if domain:
            lot_rec = self.env['stock.production.lot'].search(domain).ids
            return self.search([
                ('id', 'in', lot_rec)
            ]).name_get()
        else:
            return super(StockProductionLot, self).name_search(
                name, args, operator, limit)

    @api.model
    def get_lot_child_vals(self, record, repair):
        """

        :param record:
        :param repair:
        :return: None
        """
        if not record or not repair:
            return
        lot_version = record.lot_version + 1
        # adding the repair_part_line in parent_lot_serial number
        as_maintained = history_ids = self.env['as_maintained.history']
        for line in repair.operations:
            history_ids |= as_maintained.create({
                'lot_type': line.type,
                'repair_order_line_id': line.id,
                'as_maintained_child_lot_id': line.lot_id.id,
                'product_id': line.product_id.id,
                'price_unit': line.price_unit,
                'product_uom_qty': line.product_uom_qty,
                'location_id': line.location_id.id,
                'location_dest_id': line.location_dest_id.id,
                'as_maintained_parent_lot_id': repair.lot_id.id,
                'parent_lot_version': lot_version,
            })
        record.write({
            'lot_version': lot_version,
            'as_maintained_history_ids': [(4, history_ids.id)],
        })

    @api.onchange('lot_version')
    def onchange_lot_version(self):
        """

        :return: None
        """
        if self.lot_version > 1:
            latest_repair_rec = self.env['fleet.repair'].search(
                [], limit=1, order='create_date desc')

            def get_rec(records, lot_version, repair):
                """

                :param records:
                :param lot_version:
                :param repair:
                :return:
                """
                for lot in records:
                    self.get_lot_child_vals(lot, repair)
                    if lot.lot_ids:
                        get_rec(lot.lot_ids, lot_version, repair)

            for installed_lot in self.lot_ids:
                get_rec(installed_lot, self.lot_version, latest_repair_rec)

    @api.model
    def get_lot_serial_number(self, given_context):
        """

        :param given_context:
        :return:
        """
        domain = []
        if given_context.get('model') == 'fleet.vehicle':
            fleet_record = self.env['fleet.vehicle'].search([
                ('id', '=', given_context.get('active_id'))
            ])
            domain += [('id', '=', fleet_record.lot_id.id)]
        elif given_context.get('model') == 'stock.production.lot':
            domain += [('id', '=', given_context.get('active_id'))]
        lot_rec = self.search(domain, limit=1)
        current_user = self.user_has_groups(
            'fleet_traceability_base.group_as_maintained_configuration')
        stock_lot_list = {
            'lot_id': lot_rec.id,
            'lot_number': lot_rec.name,
            'unfoldable': True,
            'product_id': lot_rec.product_id.id,
            'product': lot_rec.product_id.name,
            'internal_reference': lot_rec.ref or '',
            'lot_version': lot_rec.lot_version,
            'is_as_maintained_user': current_user,
        }
        return stock_lot_list

    @api.model
    def get_lot_lines(self, lines, product_id):
        """

        :param lines:
        :return:
        """
        installed_location_list = []
        lot_rec = self.browse(lines)
        all_lot_rec = lot_rec._get_root_children_after_map_parent(lot_rec)
        if not all_lot_rec:
            return installed_location_list
        current_user = self.user_has_groups(
            'fleet_traceability_base.group_as_maintained_configuration')
        for lots in all_lot_rec:
            values = {
                'lot_id': lots.id,
                'lot_number': lots.name,
                'unfoldable': True,
                'product_id': lots.product_id.id,
                'product': lots.product_id.name,
                'parent_product_id': lot_rec.product_id.id,
                'parent_lot_id': lot_rec.id,
                'parent_lot_name': lot_rec.name,
                'internal_reference': lots.ref or '',
                'lot_version': lots.lot_version,
                'is_as_maintained_user': current_user,
            }
            if lots.is_non_traceable:
                values.update({
                    'non_lot_id': lots.id,
                    'is_non_traceable': lots.is_non_traceable
                })
            installed_location_list.append(values)
        return installed_location_list

    @api.model
    def get_lot_serial_ids(self):
        """

        :return:
        """
        lot_serial_number_rec = self.search([]).mapped('name')
        return {
            'lot_serial_number_rec': lot_serial_number_rec,
        } if lot_serial_number_rec else False

    @api.model
    def get_child_vals(self, record, level, parent):
        """

        :param record:
        :param level:
        :param parent:
        :return:
        """
        if not record:
            return {}
        current_user = self.user_has_groups(
            'fleet_traceability_base.group_as_maintained_configuration')
        lot_list = {
            'lot_id': record.id,
            'lot_number': record.name,
            'unfoldable': True,
            'product_id': record.product_id.id,
            'product': record.product_id.name,
            'parent_product_id': parent.product_id.id,
            'parent_lot_id': parent.id,
            'parent_lot_name': parent.name,
            'internal_reference': record.ref or '',
            'is_as_maintained_user': current_user,
            'lot_version': record.lot_version,
            'level': level
        }
        if record.is_non_traceable:
            lot_list.update({
                'non_lot_id': record.id,
                'is_non_traceable': record.is_non_traceable or False
            })
        return lot_list

    def get_child(self, records, parent, level=2):
        """

        :param records:
        :param parent:
        :param level:
        :return:
        """
        result = []

        def get_rec(lines, level, parent):
            """

            :param lines:
            :param level:
            :param parent:
            :return:
            """
            prdc_lot = self.env['stock.production.lot']
            prdc_quant = self.env['stock.production.quant']
            for l in lines:
                child = self.get_child_vals(l, level, parent)
                result.append(child)
                child_lot_ids = prdc_lot.search([
                    ('lot_ids', 'in', l.id)
                ])
                non_traceable_rec = prdc_quant.search([
                    ('lot_ids', 'in', l.id)
                ])
                if child_lot_ids:
                    level += 1
                    get_rec(child_lot_ids, level, l)
                    if level > 2:
                        level -= 1
                if non_traceable_rec:
                    for non_traceable in non_traceable_rec:
                        level += 1
                        child = self.get_child_vals(non_traceable, level, l)
                        result.append(child)
            return result
        children = get_rec(records, level, parent)
        return children

    @api.model
    def get_all_lots(self, lot_number, product_id):
        """

        :param lot_number:
        :param product_id:
        :return:
        """
        prdc_lot = self.env['stock.production.lot']
        prdc_quant = self.env['stock.production.quant']
        is_as_maintained_user = self.user_has_groups(
            'fleet_traceability_base.group_as_maintained_configuration')
        parent_lot_rec = prdc_lot.browse(lot_number)
        child_lot_ids = prdc_lot.search([
            ('lot_ids', 'in', parent_lot_rec.id)
        ])
        non_traceable_lot_ids = prdc_quant.search([
            ('lot_ids', 'in', parent_lot_rec.id)
        ])
        if not child_lot_ids and not non_traceable_lot_ids:
            return _('Not Exist.')
        lot_list = []
        # if traceable_lot exists
        if child_lot_ids:
            for lot in child_lot_ids:
                lot_rec = self.get_child(lot, parent_lot_rec)
                lot_sorted = sorted(
                    lot_rec, key=lambda i: i['level'])
                if lot_rec:
                    lot_list.append(lot_sorted)
        # if non_traceable_lot exists
        if non_traceable_lot_ids:
            for non_traceable_lot in non_traceable_lot_ids:
                lot_list.append([{
                    'non_lot_id': non_traceable_lot.id,
                    'lot_number': non_traceable_lot.name,
                    'unfoldable': True,
                    'product_id': non_traceable_lot.product_id.id,
                    'product': non_traceable_lot.product_id.name,
                    'parent_product_id': parent_lot_rec.product_id.id,
                    'parent_lot_id': parent_lot_rec.id,
                    'parent_lot_name': parent_lot_rec.name,
                    'internal_reference': non_traceable_lot.ref or '',
                    'is_as_maintained_user': is_as_maintained_user,
                    'lot_version': non_traceable_lot.lot_version,
                    'level': 2,
                    'is_non_traceable':
                        non_traceable_lot.is_non_traceable or False
                }])
        return lot_list

    def _update_as_maintained_history_version(self, version, history):
        """

        :param version:
        :param history:
        :return: None
        """
        self.write({
            'lot_version': version,
            'as_maintained_history_ids': [
                (4, history.id)
            ],
        })
        if history.origin_part_of_id != self:
            history.origin_part_of_id.lot_version += 1

    def check_lot_status(self, repair_id, service_id):
        """Check lot status.

        This method is called at the time of editing or deleting any serial/lot
        number from any RO and SR to set its lot_status.

        :param repair_id:
        :param service_id:
        :return: Boolean
        """
        self.ensure_one()
        if not self.product_id.is_serialization_product():
            return False
        prd_lot_status = self.env['stock.production.lot.status']
        domain = [
            ('lot_id', '=', self.id),
            ('stage_id.final_stage', '!=', True)
        ]
        repair_order = self.env['fleet.repair'].search(
            domain
            if not repair_id else domain + [('id', '!=', repair_id.id)]
        )
        vehicle_services = self.env['vehicle.services'].search(
            domain
            if not service_id else domain + [('id', '!=', service_id.id)]
        )
        # maintenance the lot status if repair and vehicle.
        if repair_order or vehicle_services:
            domain = [('key', '=', 'maintenance')]
        else:
            quant = self.env['stock.quant'].search([
                ('product_id', '=', self.product_id.id),
                ('lot_id', '=', self.id)
            ], limit=1)
            domain = [
                ('key', '=', 'inventory' if quant else 'available')
            ]
        lot_state = prd_lot_status.search(domain, limit=1)
        self.write({
            'stock_production_lot_status_id': lot_state.id
        })
        return True
