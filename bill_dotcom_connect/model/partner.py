from odoo import models, api, fields, _
import requests
import json


class Partner(models.Model):
    _inherit = 'res.partner'

    backend_record_id = fields.Char('Backend Record ID')

    def sync_vendor(self):
        search_partner_mode = self.env.context.get('res_partner_search_mode')
        is_supplier = search_partner_mode == 'supplier'
        obj = self.env['billdotcom.configure']
        vals = obj.test_connection()
        session_id = vals['result']['response_data']['sessionId']
        if not self.backend_record_id:
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            dict_val = {"obj": {"entity":"Vendor","isActive":"1","name":str(self.name)}}
            url = self.env['billdotcom.configure'].search([]).location
            login_end_point = str(url) + 'Crud/Create/Vendor.json'
            devkey = self.env['billdotcom.configure'].search([]).dev_key
            params_str = "devKey=" + str(devkey) + "&sessionId=" + str(session_id)+ "&data=" + str(self.mydict(dict_val))
            result = requests.post(login_end_point, data=params_str, headers=headers)
            if result.json()['response_message'] == "Success":
                data = json.loads(result.text)
                self.backend_record_id = data['response_data']['id']
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view and view.id or False
                context = dict(self._context or {})
                context['message'] = "Partner synchronized Successfully!"
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
            dict_val = {"obj": {"entity":"Vendor","id" :str(self.backend_record_id),"isActive":"1","name":str(self.name),"phone":str(self.phone)}}
            url = self.env['billdotcom.configure'].search([]).location
            login_end_point = str(url) + 'Crud/Update/Vendor.json'
            devkey = self.env['billdotcom.configure'].search([]).dev_key
            params_str = "devKey=" + str(devkey) + "&sessionId=" + str(session_id)+ "&data=" + str(self.mydict(dict_val))
            result = requests.post(login_end_point, data=params_str, headers=headers)
            if result.json()['response_message'] == "Success":
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view and view.id or False
                context = dict(self._context or {})
                context['message'] = "Synchronized Partner Updated Successfully!"
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

    class mydict(dict):
        def __str__(self):
            return json.dumps(self)

