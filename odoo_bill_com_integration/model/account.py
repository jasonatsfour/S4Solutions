from odoo import models, api, fields, _
import requests
import json
from ..unit.account_importer import Billcom_AccountImport


class Account(models.Model):
    _inherit = 'account.account'


    bill_id = fields.Char('Bill Id')
    bill_sync = fields.Boolean(string='Bill Sync', readonly=True, default=False)
    bill_account_type = fields.Integer('Bill Account Type')


    class mydict(dict):
        def __str__(self):
            return json.dumps(self)

    def importer(self, backend):
        importer = Billcom_AccountImport(backend)
        arguments = []

        # result = importer.import_account(backend,arguments)
        # if result.json()['response_message'] == "Success":
        #     account_record_list = []
        #     for record in result.json()['response_data']:
        #         if record['isActive'] == "1":
        #             if (record['accountNumber'] != None) and (int(record['accountType']) in [1,2,3,5,6,7,8,9,10,12,13,15]): #filter for if bill accountype is available in odoo
        #                 account_record_list.append(record)

        count = 0
        data = True
        account_record_list = []
        while(data):                      
            result = importer.import_account(backend,arguments,count)
            if result.json()['response_message'] == "Success" and (len(result.json()['response_data']) !=0):
                for record in result.json()['response_data']:
                    if record['isActive'] == "1":
                        if (record['accountNumber'] != None) and (int(record['accountType']) in [1,2,3,5,6,7,8,9,10,12,13,15]): #filter for if bill accountype is available in odoo
                            account_record_list.append(record)
            else:
                data = False                
            count += 100


        if account_record_list:
            for account_record in account_record_list:
                self.single_importer(backend, account_record)

    def single_importer(self,backend,account_record):
        importer = Billcom_AccountImport(backend)
        if 'id' in account_record:
            account_id = account_record['id']
        else:
            account_id = account_record #when account_record is integer
            arguments = [account_id]
            result = importer.import_account(backend,arguments)
            account_record = result.json()['response_data']

        mapper = self.env['account.account'].search([('bill_id','=',account_id)])
        if not mapper:
            mapper = self.env['account.account'].search([('code','=',account_record['accountNumber'])])
            if mapper:
                mapper.bill_id = account_record['id']
                mapper.bill_sync = True

        if mapper:
            importer.write_account(backend,mapper,account_record)
        else:
            mapper = importer.create_account(backend,mapper,account_record)

        mapper.bill_id = account_id
        mapper.bill_sync = True

