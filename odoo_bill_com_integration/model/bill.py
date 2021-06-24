from odoo import models, api, fields, _
import requests
import json
from ..unit.bill_importer import Billcom_BillImport


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    bill_id = fields.Char('Bill Id')
    bill_sync = fields.Boolean(string='Bill Sync', readonly=True, default=False)


class AccountMove(models.Model):
    _inherit = "account.move"

    bill_id = fields.Char('Bill Id')
    bill_sync = fields.Boolean(string='Bill Sync', readonly=True, default=False)

    class mydict(dict):
        def __str__(self):
            return json.dumps(self)


    def importer(self, backend):
        importer = Billcom_BillImport(backend)
        arguments = []

        # result = importer.import_bill(backend,arguments)
        # if result.json()['response_message'] == "Success":
        #     bill_record_list = []
        #     for record in result.json()['response_data']:
        #         if record['paymentStatus'] == "1" or record['paymentStatus'] == "4":
        #             if (record['item']['count'] == 0) and (record['expense']['count'] >=0) and record['isActive'] == "1":
        #                 bill_line_chartaccount_list = []#if chartOfAccountId == "0000000" then i will not import
        #                 for line in record['billLineItems']:
        #                     bill_line_chartaccount_list.append(line['chartOfAccountId'])
        #                 if bill_line_chartaccount_list:
        #                     is_import = True
        #                     for bill_line in bill_line_chartaccount_list:
        #                         if "0000000000000000" in bill_line:
        #                             is_import = False
        #                             break
        #                     if is_import == True:
        #                         bill_record_list.append(record)

        count = 0
        data = True
        bill_record_list = []
        while(data): 
            result = importer.import_bill(backend,arguments,count)
            if result.json()['response_message'] == "Success" and (len(result.json()['response_data']) !=0):
                for record in result.json()['response_data']:
                    # if record['paymentStatus'] == "1" or record['paymentStatus'] == "4":
                    if (record['item']['count'] == 0) and (record['expense']['count'] >=0) and record['isActive'] == "1":
                        bill_line_chartaccount_list = []#if chartOfAccountId == "0000000" then i will not import
                        for line in record['billLineItems']:
                            bill_line_chartaccount_list.append(line['chartOfAccountId'])
                        if bill_line_chartaccount_list:
                            is_import = True
                            for bill_line in bill_line_chartaccount_list:
                                if "0000000000000000" in bill_line:
                                    is_import = False
                                    break
                            if is_import == True:
                                bill_record_list.append(record)
            else:
                data = False                
            count += 100


        if bill_record_list:
            for bill_record in bill_record_list:
                self.single_importer(backend, bill_record)

    def single_importer(self,backend,bill_record):
        importer = Billcom_BillImport(backend)
        if 'id' in bill_record:
            bill_id = bill_record['id']
        else:
            bill_id = bill_record #when bill_record is integer
            arguments = [bill_id]
            result = importer.import_bill(backend,arguments)
            bill_record = result.json()['response_data']

        mapper = self.env['account.move'].search([('bill_id','=',bill_id)],limit=1) 

        if mapper:
            importer.write_bill(backend,mapper,bill_record)
        else:
            mapper = importer.create_bill(backend,mapper,bill_record)

        mapper.bill_id = bill_id
        mapper.bill_sync = True


