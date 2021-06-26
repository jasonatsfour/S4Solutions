import logging
from odoo import models, api, fields, _
import requests
import json
from ..unit.backend_adapter import Billcom_ImportExport
_logger = logging.getLogger(__name__)


class Billcom_VendorImport(Billcom_ImportExport):

    class mydict(dict):
        def __str__(self):
            return json.dumps(self)

    def import_vendor(self,backend,arguments,count=None):
        vals = backend.test_connection()
        session_id = vals['result']['response_data']['sessionId']
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        url = backend.location
        devkey = backend.dev_key
        if not arguments:
            login_end_point = str(url) + 'List/Vendor.json'           
            dict_val={
                        "nested" : True,
                        "start" : count,#page number
                        "max" : 100,#records per page
                    }
        else:
            login_end_point = str(url) + 'Crud/Read/Vendor.json'           
            dict_val={
                        "id" : arguments[0]
                    }

        params_str = "devKey=" + str(devkey) + "&sessionId=" + str(session_id) + "&data=" + str(self.mydict(dict_val))
        
        result = requests.post(login_end_point, data=params_str, headers=headers)
        return result



    def create_vendor(self,backend,mapper,vendor_record):
        vendor_country_id = mapper.env['res.partner'].country_id.search([('name','=',vendor_record['addressCountry'])]) 
        vendor_state_id =	mapper.env['res.partner'].state_id.search([('code','=',vendor_record['addressState']),('country_id','=',vendor_country_id.id)])		

        vals={
			'name' : vendor_record['name'] or '',
			'supplier_rank': 1,
			'email' : vendor_record['email'] or '',
			'street' : vendor_record['address1'] or '',
			'street2' : vendor_record['address2'] or '',
			'city' : vendor_record['addressCity'] or '',
			'state_id' : vendor_state_id.id or None,
			'zip' : vendor_record['addressZip'] or '',
			'country_id' : vendor_country_id.id or None,
			'phone' : vendor_record['phone'] or None,			
			}  
        res_partner = mapper.create(vals)
			
        return res_partner      

    def write_vendor(self,backend,mapper,vendor_record):
        vendor_country_id = mapper.env['res.partner'].country_id.search([('name','=',vendor_record['addressCountry'])]) 
        vendor_state_id =	mapper.env['res.partner'].state_id.search([('code','=',vendor_record['addressState']),('country_id','=',vendor_country_id.id)])		

        vals={
			'name' : vendor_record['name'] or '',
			'supplier_rank': 1,
			'email' : "pravins@gmail.com" or '',
			'street' : vendor_record['address1'] or '',
			'street2' : vendor_record['address2'] or '',
			'city' : vendor_record['addressCity'] or '',
			'state_id' : vendor_state_id.id or None,
			'zip' : vendor_record['addressZip'] or '',
			'country_id' : vendor_country_id.id or None,
			'phone' : vendor_record['phone'] or None,			
			}  
        res_partner = mapper.write(vals)
			
        return res_partner      