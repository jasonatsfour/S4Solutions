# -*- coding: utf-8 -*-

from odoo import models, fields, _, api


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    location_id = fields.Many2one('stock.location', string="Stock Location")


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    routing_id = fields.Many2one(
        'mrp.routing', 'Parent Routing',
        index=True, ondelete='cascade', required=False,
        help="The routing contains all the Work Centers used and for how long. This will create work orders afterwards "
             "which alters the execution of the manufacturing order.")
    location_id = fields.Many2one('stock.location', string="Location",
                                  related="workcenter_id.location_id", store=True)
    company_id = fields.Many2one('res.company', 'Company',  related='', readonly=False)

    @api.model
    def create(self, vals):
        res = super(MrpRoutingWorkcenter, self).create(vals)
        if self._context.get('need_to_create_wo') and self._context.get('production_id'):
            production_id = self.env['mrp.production'].browse(self._context.get('production_id'))
            vals.update({'routing_id': production_id.routing_id.id})
            production_id.create_workorder_for_given_operation(res, with_route=False)
        return res
