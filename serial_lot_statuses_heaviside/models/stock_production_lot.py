# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api


class StockProductionLot(models.Model):
    """Inherited: Lot/Serial Number

    Fields:
    wo_id: To link WO

    ORM:
    create
    """
    _inherit = 'stock.production.lot'

    wo_id = fields.Many2one('mrp.workorder', string="Work Order")

    @api.model
    def create(self, vals):
        """ORM: Create



        :param vals:
        :return:
        """
        if 'current_wo' in self._context:
            sr_id = self.search([
                ('wo_id', '=', self._context['current_wo'])
            ], limit=1)
            if sr_id and sr_id.stock_production_lot_status_id and \
                    sr_id.stock_production_lot_status_id.key == 'installed':
                status_id = self.env['stock.production.lot.status'].search([
                    ('key', '=', 'available')
                ], limit=1)
                sr_id.write({
                    'wo_id': False,
                    'stock_production_lot_status_id': status_id.id
                })
            status_id = self.env['stock.production.lot.status'].search([
                ('key', '=', 'installed')
            ], limit=1)
            vals.update({
                'wo_id': self._context['current_wo'],
                'stock_production_lot_status_id': status_id and status_id.id
            })
        res = super(StockProductionLot, self).create(vals)
        return res
