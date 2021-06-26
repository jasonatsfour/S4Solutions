# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RepairOrderCreationWizard(models.TransientModel):
    """

    """
    _name = "repair.order.creation.wiz"
    _description = "Repair Order Creation"

    @api.model
    def default_get(self, fields):
        """

        :param fields:
        :return: Default or Raise Error
        :raise: User Error
        """
        res = super(RepairOrderCreationWizard, self).default_get(fields)
        res_ids = self._context.get('active_ids', False)
        active_model = self._context.get('active_model', False)
        vehicle_ids = [
            service.vehicle_id.id
            for service in self.env[active_model].browse(res_ids)]
        stage_rec = [stage.id for stage in self.env[
            'fleet.repair.stage'].search([]) if stage.final_stage]
        if len(set(vehicle_ids)) > 1:
            raise UserError(_(
                "Please select Service(s) for the "
                "same Vehicle to create Repair order."))
        res.update({
            'vehicle_id': vehicle_ids[0],
        })
        if len(stage_rec) > 0:
            res.update({
                'stage_id': stage_rec[0],
            })
        return res

    repair_id = fields.Many2one('fleet.repair', string="Existing Repair Order")
    stage_id = fields.Many2one('fleet.repair.stage', string="Stage")
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")

    def prepare_repair_order_vals(self, service_ids, vehicle_id):
        """

        :param service_ids:
        :param vehicle_id:
        :return:
        """
        vehicle_services_ids = []
        included_services_ids = []
        unlink_included_services = []
        unlink_service_ids = []
        sr_operations = []
        for service_id in service_ids:
            vehicle_services_ids += [(0, 0, {
                'service_id': service_id.id
            })]
            for included_service in service_id.included_services_ids:
                included_services_ids += [(0, 0, {
                    'cost_subtype_id': included_service.cost_subtype_id.id,
                    'amount': included_service.amount,
                    'vehicle_id': vehicle_id.id
                })]
                if included_service.cost_subtype_id:
                    unlink_included_services.append(
                        included_service.cost_subtype_id)
            if service_id.repair_id:
                unlink_service_ids.append(service_id)
            sr_operations.extend(self._prepare_service_operations(service_id))
        vals_create = {
            'name': _('New'),
            'vehicle_id': vehicle_id.id,
            'product_id': vehicle_id.product_id.id,
            'x_location': vehicle_id.x_location.id,
            'vehicle_services_ids': vehicle_services_ids,
            'included_services_ids': included_services_ids,
            'operations': sr_operations
        }
        vals_unlink = {
            'name': _('New'),
            'vehicle_id': vehicle_id.id,
            'product_id': vehicle_id.product_id.id,
            'vehicle_services_ids': vehicle_services_ids,
            'included_services_ids': included_services_ids,
            'unlink_service_ids': unlink_service_ids,
            'unlink_included_services': unlink_included_services
        }
        return vals_create, vals_unlink

    def unlink_repair_services(self, unlink_service_ids,
                               unlink_included_services, repair_id):
        """

        :param unlink_service_ids:
        :param unlink_included_services:
        :param repair_id:
        :return:
        """
        fleet_rs = self.env['fleet.repair.service']
        fleet_vh_cost = self.env['fleet.vehicle.cost']
        for unlink_service in unlink_service_ids:
            repair_service = fleet_rs.search([
                ('service_id', '=', unlink_service.id),
                ('repair_id', '!=', repair_id.id)
            ])
            repair_service.sudo().unlink()
        for unlink_included_service in unlink_included_services:
            included_service = fleet_vh_cost.search([
                ('cost_subtype_id', '=', unlink_included_service.id),
                ('repair_id', '!=', repair_id.id)
            ])
            included_service.sudo().unlink()
        return True

    def create_repair_order(self):
        """

        :return:
        """
        repair_obj = self.env['fleet.repair']
        active_model = self._context.get('active_model', False)
        active_ids = self._context.get('active_ids', False)
        if active_model and active_ids and self.vehicle_id:
            service_ids = self.env[active_model].browse(active_ids)
            if self.repair_id:
                vehicle_services_ids = []
                unlink_included_services = []
                included_services_ids = []
                unlink_service_ids = []
                repair_id = self.repair_id
                for service_id in service_ids:
                    self._create_repair_lines_to_exist(
                        service_id, self.repair_id)
                    if service_id not in [
                        service.service_id
                        for service in repair_id.vehicle_services_ids
                    ]:
                        vehicle_services_ids += [(0, 0, {
                            'service_id': service_id.id
                        })]
                        for included_service in \
                                service_id.included_services_ids:
                            included_services_ids += [(0, 0, {
                                'cost_subtype_id':
                                    included_service.cost_subtype_id.id,
                                'amount': included_service.amount,
                                'vehicle_id': self.vehicle_id.id
                            })]
                            if included_service.cost_subtype_id:
                                unlink_included_services.append(
                                    included_service.cost_subtype_id)
                        if service_id.repair_id:
                            unlink_service_ids.append(service_id)
                self.unlink_repair_services(
                    unlink_service_ids, unlink_included_services, repair_id)
                repair_id.vehicle_services_ids = vehicle_services_ids
                repair_id.included_services_ids = included_services_ids
            else:
                vals = self.prepare_repair_order_vals(
                    service_ids, self.vehicle_id)
                repair_id = repair_obj.create(vals[0])
                if vals[1]['unlink_service_ids'] and \
                        vals[1]['unlink_included_services']:
                    self.unlink_repair_services(
                        vals[1]['unlink_service_ids'],
                        vals[1]['unlink_included_services'], repair_id)
                else:
                    for service_id in service_ids:
                        if not service_id.repair_id:
                            service_id.repair_id = repair_id.id
            repair_id.onchange_vehicle_id()
            inprogress_state = self.env['vehicle.service.state'].search([
                ('in_progress', '=', True)
            ], limit=1)
            if inprogress_state:
                service_ids.write({
                    'stage_id': inprogress_state.id
                })
            if self._context.get('open_repair', False):
                # Repair Order Action
                action = self.env.ref(
                    'fleet_kanban_services_base.fleet_repair_action_main'
                ).read()[0]
                if len(repair_id) > 1:
                    action['domain'] = [('id', 'in', repair_id.ids)]
                elif len(repair_id) == 1:
                    action['views'] = [(
                        self.env.ref(
                            'fleet_kanban_services_base.fleet_repair_view_form'
                        ).id,
                        'form'
                    )]
                    action['res_id'] = repair_id.ids[0]
                return action
            return {'type': 'ir.actions.act_window_close'}

    def _prepare_service_operations(self, service_id):
        """

        :param service_id:
        :return:
        """
        sr_operations = service_id.operations.read()
        if not sr_operations:
            return []
        for x in sr_operations:
            x.update({
                'product_id': x['product_id'][0],
                'lot_id': x['lot_id'][0] if x.get('lot_id') else False,
                'product_uom': x['product_uom'][0],
                'location_id': x['location_id'][0]
                if x['location_id'] else False,
                'location_dest_id': x['location_dest_id'][0]
                if x['location_dest_id'] else False,
                'service_request_template_id': False,
                'service_request_id': False,
            })
        return [(0, 0, x) for x in sr_operations]

    def _create_repair_lines_to_exist(self, service, repair):
        """

        :param service:
        :param repair:
        :return:
        """
        lines = self.env['fleet.repair.line']
        templ_operations = service.operations.read()
        for x in templ_operations:
            del x['id']
            x.update({
                'product_id': x['product_id'][0],
                'lot_id': x['lot_id'][0] if x.get('lot_id') else False,
                'product_uom': x['product_uom'][0],
                'location_id': x['location_id'][0],
                'location_dest_id': x['location_dest_id'][0],
                'service_request_template_id': False,
                'service_request_id': False,
                'repair_id': repair.id
            })
            lines.create(x)
