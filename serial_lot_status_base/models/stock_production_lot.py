# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api

LOCATION_STATUS = {
    'internal': 'inventory',  # Receipt Transaction/Inventory Adjustment
    'production': 'installed',  # Consumption on MO/WO
    'inventory': 'scrapped',  # LOSS
}


class StockProductionLot(models.Model):
    """Stock Production Lot

    To manage addition fields of status and other.

    Fields:
    stock_production_lot_status_id: To set status like
    Available(default) /Inventory /Installed/ Scrapped.

    Methods:
    _set_lot_status: Default status 'Available' to calling field.
    calculate_lot_status: Set based on location.
    get_root_lot: To get patent product Lot/Serial.

    ORM:
    name_search: to get lot after check Not For Flight.
    """
    _inherit = 'stock.production.lot'

    def _set_lot_status(self):
        """Default Call: Set Lot Status

        stock_production_lot_status_id: to set as Available

        :return: Recordset of stock.production.lot.status
        """
        return self.env.ref(
            'serial_lot_status_base.lot_available',
            raise_if_not_found=False)

    stock_production_lot_status_id = fields.Many2one(
        'stock.production.lot.status', string="Status",
        default=_set_lot_status)
    version = fields.Integer(string="Version", default=1)
    is_none_production = fields.Boolean(string="Not For Flight")
    lot_ids = fields.Many2many(
        'stock.production.lot', 'installed_location_rel', 'lot_id',
        'installed_location_id', string='Installed Location',
        track_visibility='onchange')

    def calculate_lot_status(self, location_id, operation_type=False):
        """Calculate Lot Status
        Here, Location id will received and checks if location is type of
        listed location than set state according to location else default
        status should 'Available'.

        internal  : Receipt Transaction/Inventory Adjustment
        production: Consumption on MO/WO
        inventory : LOSS

        :param location_id: Stock Location ID(int)
        :return: True
        """
        location_id = self.env['stock.location'].browse(location_id)
        key = 'installed' if operation_type == 'add' else LOCATION_STATUS.get(location_id.usage, 'available')
        lot_status = self.env['stock.production.lot.status'].search([
            ('key', '=', key)
        ], limit=1)
        self.write({'stock_production_lot_status_id': lot_status.id})
        return True

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """ORM: Name Search

        This method is override to get the list of lot with respected its type
        which is selected in M2O object of lot.

        It depends on context keywords.
        Keys:
        add: Allow to select any of exist
        parent_lot_id: To get for current parent lot
        remove: Allow only to select form parent children
        get_children: Allow from any children of children

        It checks for Not for Flight Boolean.

        :param name: Base
        :param args: Base
        :param operator: Base
        :param limit: Base
        :return : Recordset
        """
        domain = []
        if self._context.get('type') == 'remove' and \
                self._context.get('product_id') and \
                self._context.get('parent_lot_id'):
            domain = [
                ('product_id', '=', self._context.get('product_id')),
                ('lot_ids', 'in', self._context.get('parent_lot_id'))
            ]
        elif self._context.get('type') in ['add', 'edit'] and \
                self._context.get('product_id') and \
                self._context.get('parent_lot_id'):
            available_status = self.env['stock.production.lot.status'].search([
                ('key', 'in', ['available', 'inventory'])
            ]).ids
            domain = [
                ('id', '!=', self._context.get('parent_lot_id')),
                ('product_id', '=', self._context.get('product_id')),
                ('stock_production_lot_status_id', 'in', available_status),
                ('is_none_production', '=', False),
            ]
        elif self._context.get('get_children'):
            root = self.browse(self._context['get_children'])
            domain = [('id', 'in', root._get_root_children().ids)]
        if domain:
            lot_rec = self.search(domain).ids
            return self.search([('id', 'in', lot_rec)]).name_get()
        else:
            return super(StockProductionLot, self).name_search(
                name, args, operator, limit)
