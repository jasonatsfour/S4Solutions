# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import http
from odoo.http import request


class FleetTraceability(http.Controller):
    """Fleet Traceability Screen.

    """

    def get_available_status(self):
        """

        :return:
        """
        return request.env['stock.production.lot.status'].search([
            ('key', 'in', ['available', 'inventory'])
        ]).ids

    @http.route('/get_serial_number_list', type='json', auth='public')
    def get_serial_number_list(self, **kw):
        """

        :param kw:
        :return:
        """
        # Method to get current lot number and available lot serial number
        available_lot_status = self.get_available_status()
        parent_lot_id = request.env['stock.production.lot'].search([
            ('id', '=', kw.get('current_lot_number')),
            ('product_id', '=', kw.get('product_id'))
        ])
        values = {
            'parent_lot_number': parent_lot_id.name,
            'parent_lot_id': kw.get('current_lot_number'),
            'available_lot_status': available_lot_status,
        }
        return request.env['ir.ui.view'].render_template(
            'fleet_traceability_base.add_lot_serial_number', values)

    @http.route('/edit_lot_serial_number', type='json', auth='public')
    def edit_lot_serial_number(self, **kw):
        """

        :param kw:
        :return:
        """
        # Method to edit lot_serial_number
        lot = request.env['stock.production.lot']
        available_lot_status = self.get_available_status()
        lot_number = kw.get('lot_number', False)
        parent_lot_number = kw.get('parent_lot_number', False)
        if parent_lot_number and lot_number:
            lot_number = lot.browse(lot_number)
            parent_lot_number = lot.browse(parent_lot_number)
            values = {
                'parent_lot_id': parent_lot_number.id,
                'parent_lot_number': parent_lot_number.name,
                'current_lot_id': lot_number.id,
                'current_lot_number': lot_number.name,
                'available_lot_status': available_lot_status,
            }
            return request.env['ir.ui.view'].render_template(
                'fleet_traceability_base.edit_lot_serial_number', values)

    @http.route('/remove_lot_serial_number', type='json', auth='public')
    def remove_lot_serial_number(self, **kw):
        """Remove Serial/Lot Number

        Removes all the non-traceable entries.

        :param kw: Passes params - Lot & Parent Lot Number.
        :return: None or render the template.
        """
        lot = request.env['stock.production.lot']
        quant = request.env['stock.production.quant']
        lot_number = kw.get('lot_number', False)
        parent_lot_number = kw.get('parent_lot_number', False)
        if parent_lot_number and lot_number:
            lot_number = lot.browse(lot_number)
            non_traceable = quant.search([
                ('name', '=', lot_number.name)
            ])
            parent_lot_number = lot.browse(parent_lot_number)
            values = {
                'parent_lot_number': parent_lot_number.name,
                'lot_number': non_traceable.name,
                'non_traceable_lot_rec': non_traceable.id,
            }
            return request.env['ir.ui.view'].render_template(
                'fleet_traceability_base.remove_lot_serial_number', values)
