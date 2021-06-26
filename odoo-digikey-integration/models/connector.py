# -*- coding: utf-8 -*-

from odoo import models, fields, api

from odoo import models, fields, api, osv

from requests_oauthlib import OAuth2Session
import requests

from requests_oauthlib import OAuth2
from urllib.parse import parse_qs
from datetime import datetime

from datetime import timedelta
import json

import webbrowser
from odoo import http, SUPERUSER_ID, _
from odoo.http import request
from odoo.exceptions import UserError
import base64
from base64 import b64encode
import sys
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")


class odoo_digikey_connector(models.Model):
    _name = 'digikey.connector'
    _description = 'Digikey Backend Configuration'
    #oauth2 fields
    name=fields.Char('Name')
    client_id=fields.Char("Client Id", required=True, default="Enter Client ID")
    client_secret=fields.Char("Client secret",required=True, default="Enter Client Secret" )
    redirect_uri = fields.Char("Redirect URI", required=True, default='https://localhost/web/callback')
    oauth2_authorization_base_url = fields.Char("Authorization Base URL", required=True, default='https://api.digikey.com/v1/oauth2/authorize')
    token_url = fields.Char("Token URL", required=True, default='https://api.digikey.com/v1/oauth2/token')
    token_type = fields.Char(string='Token Type', help='Identifies the type of token returned. At this time, this field will always have the value Bearer')
    x_refresh_token_expires_in = fields.Char(string='X Refresh Token Expires In ', help='The remaining lifetime, in seconds, for the connection, after which time the user must re-grant access, See refresh_token policy for details.')
    refresh_token = fields.Char(default='refresh_token', string='Refresh Token', help='A token used when refreshing the access token.')
    access_token = fields.Char(default='token', string='Access Token', help='The token that must be used to access the QuickBooks API.')
    expires_in = fields.Char(string='Expires In', help='The remaining lifetime of the access token in seconds. The value always returned is 3600 seconds (one hour). Use the refresh token to get a fresh one')
    expires_at = fields.Char(string='Expires At', help='The remaining lifetime of the access token in seconds. The value always returned is 3600 seconds (one hour). Use the refresh token to get a fresh one. See Refreshing the access token for further information.')
    token = fields.Char(string='Token', help='The token that must be used to access the Digikey API.')
    o2_auth_url = fields.Char("Authorized Url", default="https://api.digikey.com/v1/oauth2/token")
    o2_go_to = fields.Char("Go to link", readonly=True, default='')
    app_name=fields.Char("Digikey app name")

    # # Two step oauth2 authorization 
    #@api.multi
    def digi_authorization_o2_step1(self):        
        uri=self.redirect_uri.split('/')
        if uri[-1]!='callback' or uri[-2]!='web':
            raise UserError("Please add '/web/callback' at the end of URL" )

        digi = OAuth2Session(self.client_id, redirect_uri=self.redirect_uri)
        authorization_url, state = digi.authorization_url(self.oauth2_authorization_base_url)
        self.write({'o2_go_to': authorization_url,
                    'o2_auth_url': self.o2_auth_url,})

  

    #@api.multi
    def digi_auth_o2_auto_step2(self, context):        
        obj=self.env['digikey.connector'].search([('id','=',context['id'])])       
        url = context['token_url']        
        grant_type = "authorization_code"              
        payload = {
                    'code':context['code'],      
                    'client_id':context['client_key'],
                    'client_secret':context['client_secret'],
                    'redirect_uri':context['redirect_uri'],
                    'grant_type':grant_type,
        
                }
        fetch_toke = requests.post(url, data=payload)     
       
        obj.write({'token_type':fetch_toke.json()['token_type'],
                'x_refresh_token_expires_in':fetch_toke.json()['refresh_token_expires_in'],
                'refresh_token':fetch_toke.json()['refresh_token'],
                'access_token':fetch_toke.json()['access_token'],
                'expires_in':fetch_toke.json()['expires_in'],
                # 'expires_at':fetch_toke_response('expires_at')
                })
        obj.write({'token':fetch_toke})


    #@api.multi
    def test_connection(self):      
        """ Test backend connection """
        headeroauth = OAuth2Session(self.client_id)      

        authorization = "Bearer"+" "+self.access_token

        headers={
                "X-DIGIKEY-Client-Id":self.client_id,
                "Authorization":authorization,
                # "X-DIGIKEY-Locale-Site":"US",
                # "X-DIGIKEY-Locale-Language":"en",
                # "X-DIGIKEY-Locale-Currency":"USD",
                # "X-DIGIKEY-Locale-ShipToCountry":"us",          
                "x-digikey-customer-id":self.client_id
                }
       
        api_method="https://api.digikey.com/Search/v3/Products/p5555-nd"
       
        fetch_data = headeroauth.get(api_method, headers=headers)

        if fetch_data.status_code == 200:
            keys = fetch_data.json()

        if fetch_data.status_code == 404:
            raise Warning(_("Enter Valid url"))
        val = fetch_data.json()
    
        msg = ''

        #msg = ''
        if 'errors' in fetch_data.json():
            msg = val['errors'][0]['message'] + '\n' + val['errors'][0]['code']
            raise Warning(_(msg))
        elif fetch_data.status_code == 200:
            raise UserError(_("Connection Test Succeeded! Everything seems properly set up!"))
        else:
            raise UserError(_(val['moreInformation']))


    #@api.model    
    def refresh_connection(self):      
        """ Refresh backend connection """
        self = self.env['digikey.connector'].search([])
        headeroauth = OAuth2Session(self.client_id)
        api_method = "https://api.digikey.com/v1/oauth2/token"
        headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',

                }        
        if self.client_id:
            try:
                fetch_toke=headeroauth.refresh_token(token_url="https://api.digikey.com/v1/oauth2/token", refresh_token=self.refresh_token, headers=headers, client_id=self.client_id, client_secret=self.client_secret)
            
            except Exception as e:
                raise UserError(e)
            if fetch_toke:                
                keys = fetch_toke
                self.update({'refresh_token':keys['refresh_token'],
                            'access_token':keys['access_token'],
                            'token_type':keys['token_type'],
                            'expires_in':keys['expires_in'],})
                self.update({'token':fetch_toke})
        
          
