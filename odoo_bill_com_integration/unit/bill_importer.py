import logging
from odoo import models, api, fields, _
import requests
import json
from datetime import datetime
from odoo.exceptions import UserError, RedirectWarning, ValidationError, Warning
from ..unit.backend_adapter import Billcom_ImportExport
_logger = logging.getLogger(__name__)


class Billcom_BillImport(Billcom_ImportExport):

    class mydict(dict):
        def __str__(self):
            return json.dumps(self)

    def import_bill(self,backend,arguments,count=None):
        vals = backend.test_connection()
        session_id = vals['result']['response_data']['sessionId']
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        url = backend.location
        devkey = backend.dev_key
        if not arguments:
            login_end_point = str(url) + 'List/Bill.json'           
            dict_val={
                        "nested" : True,
                        "start" : count,#page number
                        "max" : 100,#records per page
                    }
        else:
            login_end_point = str(url) + 'Crud/Read/Bill.json'           
            dict_val={
                        "id" : arguments[0]
                    }

        params_str = "devKey=" + str(devkey) + "&sessionId=" + str(session_id) + "&data=" + str(self.mydict(dict_val))
        
        result = requests.post(login_end_point, data=params_str, headers=headers)
        return result


    def create_bill(self,backend,mapper,bill_record):
        _logger.debug("Import Bill (%s)",bill_record)
        if bill_record['vendorId']:
            vendor_record = bill_record['vendorId']
            partner_id = mapper.env['res.partner'].search([('bill_id','=',vendor_record)], limit=1)
            if not partner_id:
                partner_id = mapper.env['res.partner'].single_importer(backend,vendor_record)
            
            partner_id = mapper.env['res.partner'].search([('bill_id','=',vendor_record)], limit=1)
            
            vals = {
                    'partner_id':partner_id.id,
                    'type':'in_invoice'
                }

            if bill_record['dueDate']:
                due_date = bill_record['dueDate'].split('-')
                if len(due_date) == 3:
                    vals['invoice_date_due'] = datetime(int(due_date[0]),int(due_date[1]),int(due_date[2]))
            
            if bill_record['invoiceDate']:
                invoice_date = bill_record['invoiceDate'].split('-')
                if len(due_date) == 3:
                    vals['invoice_date'] = datetime(int(invoice_date[0]),int(invoice_date[1]),int(invoice_date[2]))

            
            bill_created = mapper.create(vals)	         

            invoice_line_record_list = []
            
            for line in bill_record['billLineItems']:
                if line['chartOfAccountId']:
                    # if "0000000000000000" in line['chartOfAccountId']:
                    #     raise UserError("Chart Of Account is not added to billLineItems")
                    chartofaccount_id = mapper.env['account.account'].search([('bill_id','=',line['chartOfAccountId'])], limit=1)
                    if not chartofaccount_id:
                        account_record = line['chartOfAccountId']
                        chartofaccount_id = mapper.env['account.account'].single_importer(backend,account_record)

                    chartofaccount_id = mapper.env['account.account'].search([('bill_id','=',line['chartOfAccountId'])], limit=1)

                    is_import = True
                    if invoice_line_record_list:
                        for invoice_line in invoice_line_record_list:
                            if invoice_line[2]['account_id'] == chartofaccount_id.id:
                                invoice_line[2]['price_unit'] = invoice_line[2]['price_unit'] + line['amount']
                                invoice_line[2]['price_subtotal'] = invoice_line[2]['price_subtotal'] + line['amount']
                                is_import = False
                                break
                    if (is_import == True) or (not invoice_line_record_list):
                        result = [0,0,{
                                    'bill_id':line['id'],
                                    'bill_sync':True,
                                    'account_id': chartofaccount_id.id,
                                    'price_unit': line['amount'],
                                    'quantity': 1,
                                    'price_subtotal': line['amount'],
                                    'name':line['description'] or ''                                      
                            }]

                        invoice_line_record_list.append(result)

            if invoice_line_record_list:
                bill_created.update({'invoice_line_ids': invoice_line_record_list})

            return bill_created


    def write_bill(self,backend,mapper,bill_record):
        _logger.debug("Bill Import %s", bill_record)
        if bill_record['vendorId']:
            vendor_record = bill_record['vendorId']
            partner_id = mapper.env['res.partner'].search([('bill_id','=',vendor_record)], limit=1)
            if not partner_id:
                partner_id = mapper.env['res.partner'].single_importer(backend,vendor_record)
            
            partner_id = mapper.env['res.partner'].search([('bill_id','=',vendor_record)], limit=1)
            
            vals = {
                    'partner_id':partner_id.id,
                    # 'type':'in_invoice'
                }
            if bill_record['dueDate']:
                due_date = bill_record['dueDate'].split('-')
                if len(due_date) == 3:
                    vals['invoice_date_due'] = datetime(int(due_date[0]),int(due_date[1]),int(due_date[2]))

            if bill_record['invoiceDate']:
                invoice_date = bill_record['invoiceDate'].split('-')
                if len(due_date) == 3:
                    vals['invoice_date'] = datetime(int(invoice_date[0]),int(invoice_date[1]),int(invoice_date[2]))

            mapper.write(vals)
            mapper.invoice_line_ids.unlink()	         

            invoice_line_record_list = []
            
            for line in bill_record['billLineItems']:
                if line['chartOfAccountId']:
                    chartofaccount_id = mapper.env['account.account'].search([('bill_id','=',line['chartOfAccountId'])], limit=1)
                    if not chartofaccount_id:
                        account_record = line['chartOfAccountId']
                        chartofaccount_id = mapper.env['account.account'].single_importer(backend,account_record)

                    chartofaccount_id = mapper.env['account.account'].search([('bill_id','=',line['chartOfAccountId'])], limit=1)

                    is_import = True
                    if invoice_line_record_list:
                        for invoice_line in invoice_line_record_list:
                            if invoice_line[2]['account_id'] == chartofaccount_id.id:
                                invoice_line[2]['price_unit'] = invoice_line[2]['price_unit'] + line['amount']
                                invoice_line[2]['price_subtotal'] = invoice_line[2]['price_subtotal'] + line['amount']
                                is_import = False
                                break
                    if (is_import == True) or (not invoice_line_record_list):
                        result = [0,0,{
                                    'bill_id':line['id'],
                                    'bill_sync':True,
                                    'account_id': chartofaccount_id.id,
                                    'price_unit': line['amount'],
                                    'quantity': 1,
                                    'price_subtotal': line['amount'], 
                                    'name':line['description'] or ''                                  
                            }]

                        invoice_line_record_list.append(result)

            if invoice_line_record_list:
                mapper.update({'invoice_line_ids': invoice_line_record_list})

            return mapper
