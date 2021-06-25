# -*- coding: utf-8 -*-
from odoo import api, models, _
from urllib.request import urlopen
# from urllib2 import urlopen
import json
import logging

_logger = logging.getLogger(__name__)


class FetchSeller(models.TransientModel):
    """
    This wizard will fetch seller's octopart details from Octopart
    """
    _name = 'fetch.sellers'
    _description = 'Fetch Seller Details'

    @api.multi
    def fetch_seller_details(self):
        res = self.env['fetch.seller.detail'].search(
            [], limit=1).fetch_seller_details()
        return res


class FetchSellerDetail(models.TransientModel):
    """
    This wizard will fetch seller's octopart details from Octopart
    """
    _name = 'fetch.seller.detail'
    _description = 'Fetch Seller Details'

    @api.multi
    def fetch_seller_details(self):
        seller_obj = self.env['octopart.seller.detail']
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        sellers_dict = []
        api_key = None
        octopart_config = self.env['octopart.configuration'].search([(
            'status', '=', 'Active')], limit=1, order='id desc')
        if octopart_config:
            api_key = octopart_config.api_key
        self.env['octopart.seller.detail'].search([]).sudo().unlink()
        for product in self.env['product.template'].browse(active_ids):
            if api_key and product.sku or product.mpn:
                query = '{'

                if product.mpn:
                    query += '"mpn":"%s"' % product.mpn

                if product.sku:
                    if 'mpn' in query:
                        query += ','
                    query += '"sku":"%s"' % product.sku

                query += '}'
                fetched_list = self.fetch_detail(api_key, query) or []
                sellers_dict = sellers_dict + fetched_list

        sellers_ids = []
        for values in sellers_dict:
            sellers_ids.append(seller_obj.sudo().create(values).id)
        self._cr.commit()
        view_id = self.env.ref(
            'odoo_octopart_integration.octopart_seller_detail_tree_view')
        tree_view = {
            'name': _('Octopart Seller Details'),
            'type': 'ir.actions.act_window',
            'res_model': 'octopart.seller.detail',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(view_id.id, 'tree')],
            'domain': [('id', 'in', sellers_ids)],
        }
        return tree_view

    def fetch_detail(self, api_key, query):
        try:
            sellers_dict = []
            self.env['octopart.seller.detail'].search([]).unlink()
            octopart_url = 'http://octopart.com/api/v3/parts/match?apikey' \
                           '=%s&queries=[%s]&include[]=descriptions' % (
                               api_key, query)
            data = urlopen(octopart_url).read()
            data1 = data.decode('utf-8')
            octopart_data = json.loads(data1)
            currency = self.env.user.company_id.currency_id
            if octopart_data:
                for result in octopart_data['results']:
                    for item in result['items']:
                        description_dict = {}
                        for description in item['descriptions']:
                            source = \
                                description['attribution']['sources']
                            if source:
                                value = description['value']
                                description_dict.update({
                                    source[0]['uid']: value})
                        for offer in item['offers']:
                            uid = offer['seller']['uid']
                            if currency.name in offer['prices'] and \
                                    offer['prices'][currency.name]:
                                pricelist = offer['prices'][currency.name]
                                sku_product = self.env[
                                    'product.template'].search(
                                    [('mpn', '=', item['mpn'])],
                                    limit=1)
                                vals = {
                                    'product_tmpl_id':
                                        sku_product and sku_product.id,
                                    'name': offer['seller']['name'],
                                    'min_qty': offer['moq'],
                                    'uid': uid,
                                    'description':
                                        uid in description_dict and
                                        description_dict[uid] or '',
                                    'sku': offer['sku'],
                                    'stock':
                                        offer['in_stock_quantity'],
                                    'pkg': offer['packaging'],
                                    'last_updated':
                                        offer['last_updated'],
                                    'currency_id': currency.id,
                                }
                                for price in pricelist:
                                    if price and price[0] == 1:
                                        vals.update({
                                            'qty_1': price[1],
                                        })
                                    if price and price[0] == 10:
                                        vals.update({
                                            'qty_10': price[1],
                                        })
                                    if price and price[0] == 100:
                                        vals.update({
                                            'qty_100': price[1],
                                        })
                                    if price and price[0] == 1000:
                                        vals.update({
                                            'qty_1000': price[1],
                                        })
                                    if price and price[0] == 10000:
                                        vals.update({
                                            'qty_10000': price[1],
                                        })
                                if vals not in sellers_dict:
                                    sellers_dict.append(vals)
            return sellers_dict
        except Exception:
            pass
