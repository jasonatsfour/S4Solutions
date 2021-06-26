from odoo import models, api, fields, _
import requests
import json


class AccountMove(models.Model):
    _inherit = "account.move"

    backend_record_id = fields.Char('Backend Record ID')

    class mydict(dict):
        def __str__(self):
            return json.dumps(self)

    def sync_bills(self):
        obj = self.env['billdotcom.configure']
        vals = obj.test_connection()
        session_id = vals['result']['response_data']['sessionId']
        invoice_date = str(self.invoice_date.year) + "-" + str(self.invoice_date.month) + "-" + str(self.invoice_date.day)
        date = str(self.date.year) + "-" + str(self.date.month) + "-" + str(self.date.day)
        bill_itemlist = []
        if not self.partner_id.backend_record_id:
            self.partner_id.sync_vendor()

        for each_line in self.invoice_line_ids:
            if not each_line.product_id.backend_record_id:
                each_line.product_id.sync_product()
            billline_items = {"entity":"BillLineItem","description":each_line.name,"amount": each_line.price_subtotal,"itemId" : each_line.product_id.backend_record_id,"quantity" :each_line.quantity,"unitPrice" : each_line.price_unit}
            bill_itemlist.append(billline_items)

        if not self.backend_record_id:
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            dict_val = {"obj": {"entity":"Bill",
                                "isActive":"1",
                                "vendorId":str(self.partner_id.backend_record_id),
                                "invoiceNumber":str(self.name),
                                "invoiceDate":invoice_date,
                                "dueDate":date,
                                "poNumber": str(self.ref),
                                "billLineItems":bill_itemlist
                                }
                        }
            url = self.env['billdotcom.configure'].search([]).location
            login_end_point = str(url) + 'Crud/Create/Bill.json'
            devkey = self.env['billdotcom.configure'].search([]).dev_key
            params_str = "devKey=" + str(devkey) + "&sessionId=" + str(session_id)+ "&data=" + str(self.mydict(dict_val))
            result = requests.post(login_end_point, data=params_str, headers=headers)
            if result.json()['response_message'] == "Success":
                data = json.loads(result.text)
                self.backend_record_id = data['response_data']['id']
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view and view.id or False
                context = dict(self._context or {})
                context['message'] = "Bill Synchronized Successfully!"
                res_dict = {
                    'name': "Success",
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'sh.message.wizard',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'context': context,
                }
                return res_dict
            else:
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view and view.id or False
                context = dict(self._context or {})
                context['message'] = result.json()['response_data']['error_message']
                res_dict = {
                    'name': "Error",
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'sh.message.wizard',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'context': context,
                }
                return res_dict
        else:
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            dict_val = {"obj": {"entity": "Bill",
                                "id": str(self.backend_record_id),
                                "vendorId": str(self.partner_id.backend_record_id),
                                "invoiceNumber": str(self.name),
                                "invoiceDate": invoice_date,
                                "dueDate": date,
                                "poNumber": str(self.ref),
                                "billLineItems": bill_itemlist
                                }
                        }
            url = self.env['billdotcom.configure'].search([]).location
            login_end_point = str(url) + 'Crud/Update/Bill.json'
            devkey = self.env['billdotcom.configure'].search([]).dev_key
            params_str ="devKey=" + str(devkey) + "&sessionId=" + str(session_id)+ "&data=" + str(self.mydict(dict_val))
            result = requests.post(login_end_point, data=params_str, headers=headers)
            if result.json()['response_message'] == "Success":
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view and view.id or False
                context = dict(self._context or {})
                context['message'] = "Synchronized Bill Updated Successfully!"
                res_dict = {
                    'name': "Success",
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'sh.message.wizard',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'context': context,
                }
                return res_dict
            else:
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view and view.id or False
                context = dict(self._context or {})
                context['message'] = result.json()['response_data']['error_message']
                res_dict = {
                    'name': "Error",
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'sh.message.wizard',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'context': context,
                }
                return res_dict

    def cron_update_bill_status(self):
        obj = self.env['billdotcom.configure']
        vals = obj.test_connection()
        session_id = vals['result']['response_data']['sessionId']
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        dict_val = {"disbursementStatus" :  "0",
                    "start" : 0,
                    "max" : 100}
        url = self.env['billdotcom.configure'].search([]).location
        login_end_point = str(url) + 'ListPayments.json'
        devkey = self.env['billdotcom.configure'].search([]).dev_key
        params_str = "devKey=" + str(devkey) + "&sessionId=" + str(session_id) + "&data=" + str(self.mydict(dict_val))
        result = requests.post(login_end_point, data=params_str, headers=headers)
        if result.json()['response_message'] == "Success":
            bill_id_list = []
            for each in result.json()['response_data']['payments']:
                if each['billPays'][0]['paymentStatus'] == "2":
                    bill_id_list.append(each['billPays'][0]['billId'])
            for each_id in bill_id_list:
                obj = self.env['account.move'].search([('backend_record_id','=',each_id)])
                payment_done = self.env['account.payment'].search([('communication','=',obj.name)])
                if not payment_done:
                    payment_obj = self.env['account.payment'].create({
                            'payment_type':'outbound',
                            'partner_type':'supplier',
                            'partner_id':obj.partner_id.id,
                            'invoice_ids': [(6, 0, obj.ids)],
                            'amount':obj.amount_total,
                            'communication':obj.name,
                            'journal_id':self.env['account.journal'].search([('company_id', '=', self.env.company.id), ('type', 'in', ('bank', 'cash'))], limit=1).id,
                            'payment_method_id':self.env['account.payment.method'].search([('payment_type', '=', 'outbound')], limit=1).id
                        })
                    payment_obj.post()


class AccountMove(models.Model):
    _inherit = "account.move.line"

    backend_record_id = fields.Char('Backend Record ID')