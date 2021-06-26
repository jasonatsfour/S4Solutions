from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError, Warning,except_orm
import webbrowser
from odoo.tools.float_utils import float_is_zero, float_compare
from requests_oauthlib import OAuth2Session 

class digikey_purchase_order_line(models.Model):
	_inherit = 'purchase.order.line'

	@api.onchange('product_qty','product_uom')
	def get_details(self):				
		result = {}
		quantity_list=[]
		if not self.product_id:
			return result
		for order in self:
			if order.partner_id.name=="DigiKey" or order.partner_id.name=="Digikey" :
			
				digikey_object=self.env['digikey.connector'].search([])
				if digikey_object:
					headeroauth = OAuth2Session(digikey_object.client_id)					
					authorization = "Bearer"+" "+digikey_object.access_token

					headers={		
							"X-DIGIKEY-Client-Id":digikey_object.client_id,						
							"Authorization":authorization,						
							"X-DIGIKEY-Customer-Id":digikey_object.client_id
								
							}
					if len(order.product_id.seller_ids)>1:
						for supplier in order.product_id.seller_ids:
							if supplier.name==order.partner_id:
								seller_id=supplier
								break;
							else:
								return result
					else:
						seller_id=order.product_id.seller_ids
					
					body = seller_id.product_code					
					identification={"Client ID":"%s:Default" %(digikey_object.app_name)}					

					api_method="https://api.digikey.com/Search/v3/Products/%s"%(body)
				
					fetch_data = headeroauth.get(api_method, headers=headers)
					if fetch_data.status_code == 200:	
						keys = fetch_data.json()
						
						#fetching price table and adding to list						
						for qty in fetch_data.json()['StandardPricing']:
							quantity_list.append(qty['BreakQuantity'])
						if order.product_qty<=0:
							if seller_id.min_qty!=0:
								order.product_qty=seller_id.min_qty
							else:
								raise UserError("Product quantity must be more than 0")
						if len(quantity_list)==1:
							order.update({'price_unit':fetch_data.json()['StandardPricing'][0]['UnitPrice']})
						elif fetch_data.json()['StandardPricing']==[]:
							raise UserError(_("Product not available in Digikey"))
						else:
							
							for qty_list in range(0,len(quantity_list)-1):
								#UOM conversion
								if order.product_uom:
									new_qty=order.product_qty*order.product_uom.factor_inv
								else:
									new_qty=order.product_qty
								if new_qty!=0 :
									if new_qty < quantity_list[0]:
										order.update({'price_unit':(fetch_data.json()['StandardPricing'][0]['UnitPrice'])})
										break;
									elif quantity_list[qty_list] <=new_qty and quantity_list[qty_list+1]>=new_qty :
										if  quantity_list[qty_list+1]==new_qty :
											order.update({'price_unit':fetch_data.json()['StandardPricing'][qty_list+1]['UnitPrice']})	
										else:
											order.update({'price_unit':fetch_data.json()['StandardPricing'][qty_list]['UnitPrice']})
										break;
									#Above last quantity 
									elif new_qty>quantity_list[-1]:
										order.update({'price_unit':fetch_data.json()['StandardPricing'][len(quantity_list)-1]['UnitPrice']})
										break;	
								else:
									res={}
									break;

						return 

					elif fetch_data.status_code == 400:
						raise UserError("The specified part was not found")
					elif fetch_data.status_code == 401:
						raise UserError("Access Token validation failed. The token provided was invalid or expired.")
					elif fetch_data.status_code == 404: 
						raise UserError("Product not available in Digikey")
					return result
				else:
					raise UserError("Please complete digikey authorization")



