# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models, fields, api


class FleetVehicle(models.Model):
    """

    """
    _inherit = 'fleet.vehicle'

    lot_id = fields.Many2one('stock.production.lot',
                             string='Lot Serial Number')

    @api.onchange('product_id')
    def onchange_product_id(self):
        """

        :return:
        """
        if self.product_id:
            lot_rec = self.env['stock.production.lot'].search([
                ('product_id', '=', self.product_id.id)
            ], limit=1)
            self.lot_id = lot_rec.id

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """
        This method is used to get the list of vehicle with respected
        its product and lot serial number which is selected in SR.
        If there is no product then default will be executed.
        :param name:
        :param args:
        :param operator:
        :param limit:
        :return: RecordSet
        """
        domain = []
        if self._context.get('product_id') and \
                self._context.get('lot_id'):
            domain += [
                ('product_id', '=', self._context.get('product_id')),
                ('id', '=', self._context.get('lot_id'))
            ]
            lot_rec = self.env[
                'stock.production.lot'].search(domain)
            if lot_rec:
                vehicle_rec = self.search(
                    [('lot_id', '=', lot_rec.id)], limit=1)
                if vehicle_rec:
                    return self.search([
                        ('id', '=', vehicle_rec.id)
                    ]).name_get()
                else:
                    result = []
                    for installed_lot in lot_rec.lot_ids:

                        def get_rec(records):
                            for lot in records:
                                vehicle_rec = self.search(
                                    [('lot_id', '=', lot.id)], limit=1)
                                if vehicle_rec:
                                    result.append(vehicle_rec.id)
                                elif lot.lot_ids:
                                    get_rec(lot.lot_ids)
                            return result

                        get_rec(installed_lot)
                    if result:
                        return self.search([
                            ('id', 'in', result)
                        ]).name_get()
        else:
            return super(FleetVehicle, self).name_search(
                name, args, operator, limit)
