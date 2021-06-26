# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models, fields, api


class BomExplosion(models.Model):
    """BoM Explosion

    """
    _name = 'bom.explosion'
    _description = 'Bom Explosion'
    _inherit = ['mail.thread']
    _rec_name = 'manufacture_order_id'

    manufacture_order_id = fields.Many2one('mrp.production',
                                           string='Manufacturing Order')
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    product_id = fields.Many2one('product.product', string='Product',
                                 related='vehicle_id.product_id', store=True)
    code = fields.Char(string='Reference')
    is_fetch_product = fields.Boolean(string='Is fetched', default=False)
    bom_explosion_ids = fields.One2many(
        'bom.explosion.line', 'bom_explosion_id',
        string='BoM Explosion Lines', copy=True)

    @api.model
    def get_child_vals(self, record, level):
        """Get bom.line values.

        :param record: mrp.bom.line record
        :param level: Level of recursion
        :return: List of Dictionary
        """
        data = []
        if record.product_id.is_partial_serialization_product() and \
                record.product_id.is_product_fleet_use():
            product = self.env['product.product']
            bom_line = self.env['mrp.bom.line']
            product_tmpl_rec = []
            child = {
                'product_id': record.product_id.id,
                'partial_serialization_id':
                    record.product_id.partial_serialization_id.id,
                'level': level,
                'product_qty': record.product_qty,
            }
            data.append(child)
            product_tmpl_rec.append(record.bom_id.product_tmpl_id.id)
            product_ids = []
            while level > 0:
                level -= 1
                for product_tmpl in product_tmpl_rec:
                    if product_tmpl not in product_ids:
                        product_ids.append(product_tmpl)
                        product_rec = product.search([
                            ('product_tmpl_id', '=', product_tmpl)
                        ])
                        parent = {
                            'product_id': product_rec.id,
                            'level': level,
                        }
                        bom_line_rec = bom_line.search([
                            ('product_id', '=', product_rec.id)
                        ])
                        if len(bom_line_rec) > 1:
                            for line in bom_line_rec:
                                parent.update(
                                    {'product_qty': line.product_qty})
                                parent_bom_rec = self.env['mrp.bom'].search(
                                    [('bom_line_ids', '=', line.id)])
                                product_tmpl_rec.append(
                                    parent_bom_rec.product_tmpl_id.id)
                                data.append(parent)
        return data

    def get_child(self, records, level=0):
        """Get Child

        :param records:
        :param level:
        :return: List
        """
        result = []

        def get_rec(records, level):
            """ Get Records

            :param records:
            :param level:
            :return: List
            """
            for l in records:
                child = self.get_child_vals(l, level)
                result.append(child)
                if l.child_line_ids:
                    level += 1
                    get_rec(l.child_line_ids, level)
                    if level > 0:
                        level -= 1
            return result

        children = get_rec(records, level)
        return children

    def fetch_all_product(self):
        """Fetch All Products

        :return: None
        """
        self.is_fetch_product = True
        parent_bom_rec = self.env['mrp.bom'].search([
            ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)
        ])
        if parent_bom_rec.bom_line_ids:
            partial_list = []
            product_ids = []
            bom_exp_line = self.env['bom.explosion.line']
            for bom_line_rec in parent_bom_rec.bom_line_ids:
                product_rec = self.get_child(bom_line_rec)
                for product_list in product_rec:
                    total_qty = 1.0
                    product_sorted = sorted(
                        product_list, key=lambda i: i['level'])
                    if product_sorted:
                        for product in product_sorted:
                            total_qty *= product['product_qty']
                            if product['product_id'] not in product_ids:
                                for product_qty in range(0, int(total_qty)):
                                    product['product_qty'] = 1.0
                                    bom_ids = bom_exp_line.create(product)
                                    partial_list.append(bom_ids.id)
                            product_ids.append(product['product_id'])
            self.bom_explosion_ids = [(6, 0, partial_list)]
