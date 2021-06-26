# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import float_round


class ReportBomStructure(models.AbstractModel):
    _inherit = 'report.mrp.report_bom_structure'

    def get_product_forecasted(self, product_id, warehouse_id):
        po_domain = [('company_id', '=', self.env.user.company_id.id)]
        forecast_qty = 0.0
        if warehouse_id:
            picking_type_ids = self.env['stock.picking.type'].sudo().search_read([('warehouse_id', '=', warehouse_id)], ['id'])
            picking_type_ids = [x['id'] for x in picking_type_ids]
            if warehouse_id and not picking_type_ids:
                return forecast_qty
            if picking_type_ids:
                po_domain.append(('picking_type_id', 'in', picking_type_ids))
        po_ids = self.env['purchase.order'].search_read(po_domain, ['id'])
        po_ids = [x['id'] for x in po_ids]
        if po_ids:
            picking_ids = self.env['stock.picking'].search([
                ('purchase_id', 'in', po_ids), ('state', 'not in', ['done', 'cancel', 'draft'])
            ]).ids
            picking_line_ids = self.env['stock.move'].search([
                ('product_id', '=', product_id), ('picking_id', 'in', picking_ids), ('state', '!=', 'done')
            ])
            for picking_line in picking_line_ids:
                forecast_qty += picking_line.product_uom_qty
        return forecast_qty

    def get_product_pre_inspection(self, product_id, warehouse_id):
        location_ids = []
        if warehouse_id:
            warehouse_id = self.env['stock.warehouse'].sudo().browse(warehouse_id)
            if warehouse_id.lot_stock_id:
                location_ids.append(warehouse_id.lot_stock_id.id)
        if warehouse_id:
            temp = True
            loc_ids = location_ids
            while temp:
                loc_ids = self.env['stock.location'].sudo().search([('location_id', 'in', loc_ids)]).ids
                if loc_ids:
                    location_ids += loc_ids
                else:
                    temp = False
            location_ids = self.env['stock.location'].sudo().search([
                ('x_preinspection', '=', True), ('id', 'in', location_ids)
            ]).ids
        else:
            location_ids = self.env['stock.location'].sudo().search([('x_preinspection', '=', True)]).ids
        stock_quant_ids = self.env['stock.quant'].sudo().search(
            [('product_id', '=', product_id), ('location_id', 'in', location_ids)])
        qty_available = 0.0
        for quant in stock_quant_ids:
            qty_available += quant.quantity
        return qty_available

    def get_product_warehouse_stock(self, product_id, warehouse_id):
        location_ids = []
        warehouse_id = self.env['stock.warehouse'].sudo().browse(warehouse_id)
        if warehouse_id.lot_stock_id:
            location_ids.append(warehouse_id.lot_stock_id.id)
        if location_ids:
            temp = True
            loc_ids = location_ids
            while temp:
                loc_ids = self.env['stock.location'].sudo().search([('location_id', 'in', loc_ids)]).ids
                if loc_ids:
                    location_ids += loc_ids
                else:
                    temp = False
        stock_quant_ids = self.env['stock.quant'].sudo().search(
            [('product_id', '=', product_id), ('location_id', 'in', location_ids)])
        qty_available = 0.0
        for quant in stock_quant_ids:
            qty_available += quant.quantity
        return qty_available

    def _get_bom(self, bom_id=False, product_id=False, line_qty=False, line_id=False, level=False):
        bom = self.env['mrp.bom'].browse(bom_id)
        bom_quantity = line_qty
        if line_id:
            current_line = self.env['mrp.bom.line'].browse(int(line_id))
            bom_quantity = current_line.product_uom_id._compute_quantity(line_qty, bom.product_uom_id)
        # Display bom components for current selected product variant
        if product_id:
            product = self.env['product.product'].browse(int(product_id))
        else:
            product = bom.product_id or bom.product_tmpl_id.product_variant_id
        if product:
            attachments = self.env['mrp.document'].search(['|', '&', ('res_model', '=', 'product.product'),
                                                           ('res_id', '=', product.id), '&',
                                                           ('res_model', '=', 'product.template'),
                                                           ('res_id', '=', product.product_tmpl_id.id)])
        else:
            product = bom.product_tmpl_id
            attachments = self.env['mrp.document'].search(
                [('res_model', '=', 'product.template'), ('res_id', '=', product.id)])
        operations = self._get_operation_line(bom.routing_id,
                                              float_round(bom_quantity / bom.product_qty, precision_rounding=1,
                                                          rounding_method='UP'), 0)
        company = bom.company_id or self.env.company
        if 'Warehouse' in self.env.context and self.env.context['Warehouse']:
            if int(self.env.context['Warehouse']):
                qty_available = self.get_product_warehouse_stock(product.id, int(self.env.context['Warehouse']))
                qty_pre_available = self.get_product_pre_inspection(product.id, int(self.env.context['Warehouse']))
                qty_forecasted = self.get_product_forecasted(product.id, int(self.env.context['Warehouse']))
            else:
                qty_available = product.qty_available
                qty_pre_available = self.get_product_pre_inspection(product.id, False)
                qty_forecasted = self.get_product_forecasted(product.id, False)
        else:
            qty_available = product.qty_available
            qty_pre_available = self.get_product_pre_inspection(product.id, False)
            qty_forecasted = self.get_product_forecasted(product.id, False)
        qty_avail = ''
        if qty_available < bom_quantity:
            qty_avail = 'color:red;'
        lines = {
            'bom': bom,
            'bom_qty': bom_quantity,
            'bom_prod_name': product.display_name,
            'qty_available': qty_available,
            'qty_pre_available': qty_pre_available,
            'qty_avail': qty_avail,
            'qty_forecasted': qty_forecasted,
            'is_purchase': product.purchase_ok,
            'currency': company.currency_id,
            'product': product,
            'code': bom and bom.display_name or '',
            'price': product.uom_id._compute_price(product.with_context(force_company=company.id).standard_price,
                                                   bom.product_uom_id) * bom_quantity,
            'total': sum([op['total'] for op in operations]),
            'level': level or 0,
            'operations': operations,
            'operations_cost': sum([op['total'] for op in operations]),
            'attachments': attachments,
            'operations_time': sum([op['duration_expected'] for op in operations])
        }
        components, total = self._get_bom_lines(bom, bom_quantity, product, line_id, level)
        lines['components'] = components
        lines['total'] += total
        return lines

    def _get_bom_lines(self, bom, bom_quantity, product, line_id, level):
        components = []
        total = 0
        for line in bom.bom_line_ids:
            line_quantity = (bom_quantity / (bom.product_qty or 1.0)) * line.product_qty
            if line._skip_bom_line(product):
                continue
            company = bom.company_id or self.env.company
            price = line.product_id.uom_id._compute_price(
                line.product_id.with_context(force_company=company.id).standard_price,
                line.product_uom_id) * line_quantity
            if line.child_bom_id:
                factor = line.product_uom_id._compute_quantity(line_quantity,
                                                               line.child_bom_id.product_uom_id) / line.child_bom_id.product_qty
                sub_total = self._get_price(line.child_bom_id, factor, line.product_id)
            else:
                sub_total = price
            sub_total = self.env.company.currency_id.round(sub_total)
            if 'Warehouse' in self.env.context and self.env.context['Warehouse'] and int(self.env.context['Warehouse']):
                qty_available = self.get_product_warehouse_stock(line.product_id.id, int(self.env.context['Warehouse']))
                qty_pre_available = self.get_product_pre_inspection(line.product_id.id, int(self.env.context['Warehouse']))
                qty_forecasted = self.get_product_forecasted(line.product_id.id, int(self.env.context['Warehouse']))
            else:
                qty_available = line.product_id.qty_available
                qty_pre_available = self.get_product_pre_inspection(line.product_id.id, False)
                qty_forecasted = self.get_product_forecasted(line.product_id.id, False)
            qty_avail = 0
            if qty_available < line_quantity:
                qty_avail = 'color:red;'
            components.append({
                'prod_id': line.product_id.id,
                'prod_name': line.product_id.display_name,
                'qty_available': qty_available,
                'qty_pre_available': qty_pre_available,
                'qty_avail': qty_avail,
                'qty_forecasted': qty_forecasted,
                'is_purchase': line.product_id.purchase_ok,
                'code': line.child_bom_id and line.child_bom_id.display_name or '',
                'prod_qty': line_quantity,
                'prod_uom': line.product_uom_id.name,
                'prod_cost': company.currency_id.round(price),
                'parent_id': bom.id,
                'line_id': line.id,
                'level': level or 0,
                'total': sub_total,
                'child_bom': line.child_bom_id.id,
                'phantom_bom': line.child_bom_id and line.child_bom_id.type == 'phantom' or False,
                'attachments': self.env['mrp.document'].search(['|', '&',
                                                                ('res_model', '=', 'product.product'),
                                                                ('res_id', '=', line.product_id.id), '&',
                                                                ('res_model', '=', 'product.template'),
                                                                ('res_id', '=', line.product_id.product_tmpl_id.id)]),

            })
            total += sub_total
        return components, total

    def _get_pdf_line(self, bom_id, product_id=False, qty=1, child_bom_ids=[], unfolded=False):

        data = self._get_bom(bom_id=bom_id, product_id=product_id.id, line_qty=qty)

        def get_sub_lines(bom, product_id, line_qty, line_id, level):
            data = self._get_bom(bom_id=bom.id, product_id=product_id.id, line_qty=line_qty, line_id=line_id,
                                 level=level)
            bom_lines = data['components']
            lines = []

            for bom_line in bom_lines:
                qty_avail = 0
                if bom_line['qty_available'] < bom_line['prod_qty']:
                    qty_avail = 'color:red;'
                lines.append({
                    'name': bom_line['prod_name'],
                    'type': 'bom',
                    'quantity': bom_line['prod_qty'],
                    'uom': bom_line['prod_uom'],
                    'prod_cost': bom_line['prod_cost'],
                    'bom_cost': bom_line['total'],
                    'level': bom_line['level'],
                    'code': bom_line['code'],
                    'child_bom': bom_line['child_bom'],
                    'prod_id': bom_line['prod_id'],
                    'qty_available': bom_line['qty_available'],
                    'is_purchase': bom_line['is_purchase'],
                    'qty_pre_available': bom_line['qty_pre_available'],
                    'qty_forecasted': bom_line['qty_forecasted'],
                    'qty_avail': qty_avail,
                })
                if bom_line['child_bom'] and (unfolded or bom_line['child_bom'] in child_bom_ids):
                    line = self.env['mrp.bom.line'].browse(bom_line['line_id'])
                    lines += (get_sub_lines(line.child_bom_id, line.product_id, bom_line['prod_qty'], line, level + 1))
            if data['operations']:
                lines.append({
                    'name': _('Operations'),
                    'type': 'operation',
                    'quantity': data['operations_time'],
                    'uom': _('minutes'),
                    'bom_cost': data['operations_cost'],
                    'level': level,
                })
                for operation in data['operations']:
                    if unfolded or 'operation-' + str(bom.id) in child_bom_ids:
                        lines.append({
                            'name': operation['name'],
                            'type': 'operation',
                            'quantity': operation['duration_expected'],
                            'uom': _('minutes'),
                            'bom_cost': operation['total'],
                            'level': level + 1,
                        })
            return lines

        bom = self.env['mrp.bom'].browse(bom_id)
        product = product_id or bom.product_id or bom.product_tmpl_id.product_variant_id
        pdf_lines = get_sub_lines(bom, product, qty, False, 1)
        data['components'] = []
        data['lines'] = pdf_lines
        return data

    @api.model
    def _get_report_data(self, bom_id, searchQty=0, searchVariant=False):
        lines = {}
        bom = self.env['mrp.bom'].browse(bom_id)
        bom_quantity = searchQty or bom.product_qty
        bom_product_variants = {}
        bom_uom_name = ''

        if bom:
            bom_uom_name = bom.product_uom_id.name

            # Get variants used for search
            if not bom.product_id:
                for variant in bom.product_tmpl_id.product_variant_ids:
                    bom_product_variants[variant.id] = variant.display_name

        lines = self._get_bom(bom_id, product_id=searchVariant, line_qty=bom_quantity, level=1)
        return {
            'lines': lines,
            'variants': bom_product_variants,
            'bom_uom_name': bom_uom_name,
            'bom_qty': bom_quantity,
            'is_variant_applied': self.env.user.user_has_groups('product.group_product_variant') and len(
                bom_product_variants) > 1,
            'is_uom_applied': self.env.user.user_has_groups('uom.group_uom')
        }

    @api.model
    def get_html(self, bom_id=False, searchQty=1, searchVariant=False):
        res = self._get_report_data(bom_id=bom_id, searchQty=searchQty, searchVariant=searchVariant)
        warehouse_ids = self.env['stock.warehouse'].sudo().search([('company_id', '=', self.env.user.company_id.id)])
        warehouse_data = []
        for warehouse in warehouse_ids:
            warehouse_data.append({
                'id': warehouse.id,
                'name': warehouse.name
            })
        res['warehouse_data'] = warehouse_data
        res['lines']['report_type'] = 'html'
        res['lines']['report_structure'] = 'all'
        res['lines']['has_attachments'] = res['lines']['attachments'] or any(
            component['attachments'] for component in res['lines']['components'])
        res['lines'] = self.env.ref('mrp.report_mrp_bom').render({'data': res['lines']})
        return res
