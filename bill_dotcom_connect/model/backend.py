from odoo import models, api, fields, _
import requests
import json

class Billdotcom_configure(models.Model):

    """ Models for Bill.com configuration """
    _name = "billdotcom.configure"
    _description = 'Billdotcom Backend Configuration'

    name = fields.Char(string='name')
    location = fields.Char("Url")
    username = fields.Char("User Name")
    password = fields.Char("Password")
    org_key = fields.Char("Organization Key")
    dev_key = fields.Char("Developer Key")

    def test_connection(self):
        record = self.search([])
        params_str = "userName=" + str(record.username) + "&password=" + str(record.password) + "&orgId=" + str(record.org_key) + "&devKey=" + str(record.dev_key)
        url = record.location
        login_end_point = str(url) + 'Login.json'
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        result = requests.post(login_end_point, data=params_str, headers=headers)
        if result.json()['response_message'] == "Success":
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view and view.id or False
            context = dict(self._context or {})
            context['message'] = "Connection Established Successfully!"
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
                'result': result.json()
            }
            return res_dict
        else:
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view and view.id or False
            context = dict(self._context or {})
            context['message'] = result.json()['response_data']['error_message']
            res_dict = {
                'name': "Warning",
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sh.message.wizard',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': context,
                'result': result.json()
            }
            return res_dict

    class mydict(dict):
        def __str__(self):
            return json.dumps(self)

