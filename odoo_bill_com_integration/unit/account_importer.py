import logging
from odoo import models, api, fields, _
import requests
import json
from ..unit.backend_adapter import Billcom_ImportExport
_logger = logging.getLogger(__name__)

# chart of account import
class Billcom_AccountImport(Billcom_ImportExport):

    class mydict(dict):
        def __str__(self):
            return json.dumps(self)

    def import_account(self,backend,arguments,count=None):
        vals = backend.test_connection()
        session_id = vals['result']['response_data']['sessionId']
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        url = backend.location
        devkey = backend.dev_key
        if not arguments:
            login_end_point = str(url) + 'List/ChartOfAccount.json'           
            dict_val={
                        "nested" : True,
                        "start" : count,#page number
                        "max" : 100,#records per page
                    }
        else:
            login_end_point = str(url) + 'Crud/Read/ChartOfAccount.json'           
            dict_val={
                        "id" : arguments[0]
                    }

        params_str = "devKey=" + str(devkey) + "&sessionId=" + str(session_id) + "&data=" + str(self.mydict(dict_val))
        
        result = requests.post(login_end_point, data=params_str, headers=headers)
        return result


    bill_account_type_list={
        '0' : 'Unspecified',
        '1' : 'AccountsPayable',
        '2' : 'AccountsReceivable',
        '3' : 'Bank',
        '4' : 'CostofGoodsSold',
        '5' : 'CreditCard',
        '6' : 'Equity',
        '7' : 'Expense',
        '8' : 'FixedAsset',
        '9' : 'Income',
        '10' : 'LongTermLiability',
        '11' : 'OtherAsset',
        '12' : 'OtherCurrentAsset',
        '13' : 'OtherCurrentLiability',
        '14' : 'OtherExpense',
        '15' : 'OtherIncome',
        '16' : 'NonPosting',
    }

    def get_odoo_account_type_id(self,mapper,user_type):
        if user_type == '1':
            user_type_name = 'Payable'
        elif user_type == '2':
            user_type_name = 'Receivable'
        elif user_type == '3':
            user_type_name = 'Bank and Cash'
        elif user_type == '5':
            user_type_name = 'Credit Card'
        elif user_type == '6':
            user_type_name = 'Equity'
        elif user_type == '7':
            user_type_name = 'Expenses'
        elif user_type == '8':
            user_type_name = 'Fixed Asset'
        elif user_type == '9':
            user_type_name = 'Income'
        elif user_type == '12':
            user_type_name = 'Non-current Assets'
        elif user_type == '13':
            user_type_name = 'Non-current Liabilities'
        elif user_type == '15':
            user_type_name = 'Other Income'
        
        account_type_obj = mapper.env['account.account.type'].search([('name','=',user_type_name)])
        return account_type_obj

    def create_account(self,backend,mapper,account_record):
        user_type = account_record['accountType']
        odoo_account_type_id = self.get_odoo_account_type_id(mapper,user_type)

        vals = {
            'name':account_record['name'],
            'code':account_record['accountNumber'],
            'user_type_id':odoo_account_type_id.id,
            'bill_account_type':account_record['accountType'],
        }
        account = mapper.create(vals)			
        return account   
        

    def write_account(self,backend,mapper,account_record):
        user_type = account_record['accountType']
        odoo_account_type_id = self.get_odoo_account_type_id(mapper,user_type)

        vals = {
            'name':account_record['name'],
            'code':account_record['accountNumber'],
            'user_type_id':odoo_account_type_id.id,
            'bill_account_type':account_record['accountType'],
        }
        account = mapper.write(vals)
        return account  
       