# -*- coding: utf-8 -*-

from odoo import api, models


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        domain = []
        if args is None:
            args = []
        if self._context.get('routing_id', False) and self._context.get('production_id', False):
            production_id = self.env['mrp.production'].browse(self._context.get('production_id', False))
            total_operations = production_id.workorder_ids.filtered(
                lambda wo: wo.state != 'done' and wo.operation_id.id != self._context.get('operation_id', False)
            ).mapped('operation_id')
            domain = [('id', 'in', total_operations.ids)]
        return super(
            MrpRoutingWorkcenter, self).name_search(
            name, args=args + domain, operator=operator, limit=limit)
