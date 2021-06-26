# -*- coding: utf-8 -*-

import json
import logging
import werkzeug
from odoo import http, tools, _
from odoo.http import request
from odoo.exceptions import ValidationError,UserError
from odoo.addons.website_form.controllers.main import WebsiteForm
class DigikeyOdooConnector(http.Controller):
	@http.route('/web/callback', type='http', auth='none', website=True)
	def get_authorized_url(self, state, code, **kw):
		res = request.env['digikey.connector'].sudo().search([])
		res.write({
			'o2_auth_url': res.redirect_uri+'?'
			})
		context = {
			'id':str(res.id),
			'client_key':str(res.client_id), 
			'client_secret':str(res.client_secret),
			'redirect_uri':str(res.redirect_uri),
			'o2_auth_url':str(res.o2_auth_url),
			'token_url': str(res.token_url),
			'code':code
		}		
		res.digi_auth_o2_auto_step2(context)
		return werkzeug.utils.redirect('/')
		