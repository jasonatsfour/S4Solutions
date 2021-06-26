# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import api,models, _
from odoo.exceptions import UserError


class ProductionLot(models.Model):
    """

    """
    _inherit = 'stock.production.lot'

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        domain = []
        if self._context.get('from_split_wizard') and \
                (self._context.get('production_id') or self._context.get('workorder_id')):
            production_id = self.env['mrp.production'].browse(self._context.get('production_id'))
            final_production_id = production_id if production_id else \
                self.env['mrp.workorder'].browse(self._context.get('workorder_id')).production_id
            processed_lot_ids = final_production_id.move_raw_ids.mapped('move_line_ids').mapped('lot_produced_ids')
            domain += [('id', 'in', processed_lot_ids.ids)]
        args += domain
        return super(ProductionLot, self)._search(args, offset, limit, order, count=count,
                                                  access_rights_uid=access_rights_uid)

    def action_open_quants(self):
        """

        :return:
        """
        ctx = self._context.copy()
        ctx.update({'active_lot_id': self.id})
        return self.product_id.with_context(ctx).action_open_quants()

    def action_update_quantity_on_hand(self):
        """

        :return: Dictionary of Action or Raise Error
        :raise: User Error
        """
        company = self.env.user.company_id
        lot_ids = self.search([
            '|',
            ('id', '=', self.id),
            ('lot_ids', 'in', self.id)
        ])
        if not company.supplier_location_id:
            raise UserError(_(
                'Please configure Default Location '
                'for purchased product components.'))
        action = {
            'name': _('Update Installed Lots / Serial'),
            'view_type': 'tree',
            'view_mode': 'list',
            'view_id': self.env.ref(
                'manufacturing_traceability_base.'
                'view_stock_sub_assemblies_tree_editable').id,
            'res_model': 'stock.quant',
            'type': 'ir.actions.act_window',
            'context': dict(
                self.env.context,
                default_location_id=company.supplier_location_id.id,
                default_installed_lot=True,
                defualt_company_id=company.id,
                inventory_mode=True
            ),
            'domain': lot_ids and [
                ('lot_id', 'in', lot_ids.ids),
                ('quantity', '>=', 0)
            ] or [],
            'help': """
            <p class="o_view_nocontent_empty_folder">No Stock On Hand</p>
            <p>This analysis gives you an overview of the current stock
            level of your products.</p>"""
        }
        return action

    def _check_create(self):
        """

        Override this method to check the product is partial serialization or
        not at the time of creating lot from work order.

        :return:
        :raise: User Error
        """
        active_mo_id = self.env.context.get('active_mo_id')
        active_product_id = self.env.context.get('default_product_id')
        if active_mo_id:
            active_mo = self.env['mrp.production'].browse(active_mo_id)
            active_product = self.env['product.product'].browse(
                active_product_id)

            # if the product is manufacture_use then
            # it will allow to create the lot number from work order.
            if not active_mo.picking_type_id.use_create_components_lots and \
                    not active_product.partial_serialization_id \
                            .manufacturing_use:
                raise UserError(_(
                    'You are not allowed to create or edit a lot or serial '
                    'number for the components with the operation type '
                    '"Manufacturing". To change this, go on the operation '
                    'type and tick the box "Create New Lots/Serial '
                    'Numbers for Components".'))
