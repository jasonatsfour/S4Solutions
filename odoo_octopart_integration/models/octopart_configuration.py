# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning
from urllib.request import urlopen
from odoo.tools import ustr
import requests
import json


class OctopartConfiguration(models.Model):
    _name = 'octopart.configuration'
    _rec_name = 'sequence'
    _order = 'id desc'

    sequence = fields.Char(string='Sequence', default='/')
    api_key = fields.Char(string='Api Key')
    status = fields.Char(string='Status', default='InActive')
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('api_key_uniq', 'unique (api_key)', 'Api key must be unique !'),
    ]

    @api.model
    def create(self, values):
        if values.get('sequence', '/') == '/':
            values['sequence'] = self.env['ir.sequence'].next_by_code(
                'octopart.sequence') or '/'
        return super(OctopartConfiguration, self).create(values)

    def test_connection(self):
        url = 'https://octopart.com/api/v3/parts/match?apikey=%s&queries=' \
              '[{"mpn":"SN74S74N"}]&pretty_print=true' % (self.api_key)
        try:
            data = requests.get(url)
            self._cr.commit()
        except Exception as e:
            self.status = 'InActive'
            self._cr.commit()
            raise UserError(_(
                "Connection Test Failed! Here is what we got instead:\n %s"
            ) % ustr(e))
        if data.ok:
            self.status = 'Active'
            self._cr.commit()
            raise UserError(_(
                "Connection Test Succeeded! Everything seems properly set up!"
            ))
        else:
            self.status = 'InActive'
            self._cr.commit()
            raise UserError(_(
                "Connection Test Failed! Please check with your API Key!"))

    def fetch_octopart_api_details(self, vendor, product, qty, pricelist,
                                   product_code=''):
        if not vendor or not qty:
            return False

        if not vendor.octopart:
            return False

        uid = ''
        query = '{'

        if product and product.mpn:
            query += '"mpn":"%s"' % product.mpn

        if pricelist and pricelist.product_code:
            if 'mpn' in query:
                query += ','
            query += '"sku":"%s"' % pricelist.product_code
        elif product and product.sku:
            if 'mpn' in query:
                query += ','
            query += '"sku":"%s"' % product.sku
        elif product_code:
            if 'mpn' in query:
                query += ','
            query += '"sku":"%s"' % product_code

        query += '}'

        if vendor.octopart_id:
            uid = vendor.octopart_id

        if not uid:
            return False

        code = pricelist and pricelist.product_code or product_code
        if product.mpn or product.sku or code:
            try:
                octopart_url = \
                    'http://octopart.com/api/v3/parts/match?apikey=%s' \
                    '&queries=[%s]' % (self.api_key, query)
                self._cr.commit()
                data = urlopen(octopart_url).read()
                data1 = data.decode('utf-8')
                octopart_data = json.loads(data1)
                price = None
                currency = self.env.user.company_id.currency_id.name
                if octopart_data:
                    for result in octopart_data['results']:
                        for item in result['items']:
                            moq_list = [offer['moq'] for offer in item[
                                'offers'] if offer['moq'] and offer[
                                'seller']['uid'] == uid]
                            use_moq = self.is_less_than(moq_list, qty)
                            for offer in item['offers']:
                                if offer['seller']['uid'] == uid:
                                    if currency in offer['prices'] and \
                                            offer['prices'][currency]:
                                        quantity_list = \
                                            [price[0] for price in
                                             offer['prices'][currency]]
                                        nearby_value = self.is_less_than(
                                            quantity_list, qty)
                                        if use_moq and use_moq == offer['moq']:
                                            for pricelist in \
                                                    offer['prices'][currency]:
                                                if pricelist[0] == \
                                                        nearby_value:
                                                    price = pricelist[1]
                                                    return {
                                                        'price': float(price),
                                                        # 'moq': nearby_value
                                                        }
                                        else:
                                            return {
                                                'price': offer['prices'][currency][0][1],
                                            }
                                    else:
                                        raise Warning(_(
                                            "Sorry! Price not fetched from "
                                            "octopart as price is not "
                                            "available in company's currency"))
                    if not price:
                        raise Warning(_(
                            "Sorry! Your required quantity is less than "
                            "vendor's MOQ"))
            except Exception as e:
                raise Warning(_(e))

    def is_less_than(self, list, num):
        result_list = [i for i in list if i <= num]
        return result_list and max(result_list)
