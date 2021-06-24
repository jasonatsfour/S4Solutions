from odoo import models, api, fields, _
import requests
import json
from ..unit.vendor_importer import Billcom_VendorImport



class Partner(models.Model):
    _inherit = 'res.partner'


    bill_id = fields.Char('Bill Id')
    bill_sync = fields.Boolean(string='Bill Sync', readonly=True, default=False)


    class mydict(dict):
        def __str__(self):
            return json.dumps(self)

    def importer(self, backend):
        importer = Billcom_VendorImport(backend)
        arguments = []

        # result = importer.import_vendor(backend,arguments)

        # if result.json()['response_message'] == "Success":
        #     vendor_record_list = []
        #     for record in result.json()['response_data']:
        #         if record['isActive'] == "1":
        #             vendor_record_list.append(record)
        count = 0
        data = True
        vendor_record_list = []
        while(data):                      
            result = importer.import_vendor(backend,arguments,count)
            if result.json()['response_message'] == "Success" and (len(result.json()['response_data']) !=0):
                for record in result.json()['response_data']:
                    if record['isActive'] == "1":
                        vendor_record_list.append(record)
            else:
                data = False                
            count += 100
        
        if vendor_record_list:
            for vendor_record in vendor_record_list:
                self.single_importer(backend, vendor_record)

    def single_importer(self,backend,vendor_record):
        importer = Billcom_VendorImport(backend)
        if 'id' in vendor_record:
            vendor_id = vendor_record['id']
        else:
            vendor_id = vendor_record #when vendor_record is integer
            arguments = [vendor_id]
            result = importer.import_vendor(backend,arguments)
            vendor_record = result.json()['response_data']

        mapper = self.env['res.partner'].search([('bill_id','=',vendor_id)])        

        if mapper:
            importer.write_vendor(backend,mapper,vendor_record)
        else:
            mapper = importer.create_vendor(backend,mapper,vendor_record)

        mapper.bill_id = vendor_id
        mapper.bill_sync = True
