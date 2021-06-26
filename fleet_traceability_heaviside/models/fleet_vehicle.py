# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models, fields


class FleetVehicle(models.Model):
    """

    """
    _inherit = 'fleet.vehicle'

    fleet_bom_explosion_count = fields.Float(
        compute='_compute_count_bom_explosion')

    def write(self, vals):
        """ORM: Write

        Override Write Method to update the cumulative flight hours in
        Lot/Serial number and its installed location whenever a new
        x_flight_hours is updated in vehicle.

        :param vals: Dictionary of values
        :return: Super call
        """
        if 'x_flight_hours' in vals and vals.get('x_flight_hours'):
            cal_flight_hours = float(
                vals.get('x_flight_hours') - self.x_flight_hours)
            if self.lot_id:
                lot_rec = [self.lot_id]
                installed_lot_rec = self.env['stock.production.lot'].search([
                    ('lot_ids', '=', self.lot_id.id)
                ])
                for installed_lot in installed_lot_rec:
                    lot_rec.append(installed_lot)

                    def get_rec(records):
                        """Get Records.

                        :param records:
                        """
                        serial = self.env['stock.production.lot']
                        for data in records:
                            if data not in lot_rec:
                                lot_rec.append(data)
                            child_lot_rec = serial.search([
                                ('lot_ids', '=', data.id)
                            ])
                            if child_lot_rec:
                                get_rec(child_lot_rec)

                    get_rec(installed_lot)

                for lot in lot_rec:
                    lot.cumulative_flight_hours = lot.cumulative_flight_hours + cal_flight_hours

        return super(FleetVehicle, self).write(vals)

    def _compute_count_bom_explosion(self):
        """

        """
        bom_explosion = self.env['bom.explosion']
        for record in self:
            record.fleet_bom_explosion_count = bom_explosion.search_count([
                ('vehicle_id', '=', record.id),
                ('product_id', '=', record.product_id.id)
            ])

    def return_action_to_open_bom_explosion(self):
        """Open Vehicle

        This opens the xml view specified in xml_id for the current vehicle.

        :return: Act Window or Boolean
        """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window'].for_xml_id(
                'fleet_traceability', xml_id)
            res.update(
                context=dict(self.env.context,
                             default_vehicle_id=self.id, group_by=False),
                domain=[('vehicle_id', '=', self.id),
                        ('product_id', '=', self.product_id.id)]
            )
            return res
        return False
