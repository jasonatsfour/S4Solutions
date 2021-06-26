# -*- coding: utf-8 -*-
from odoo import http

# class ZipProduct(http.Controller):
#     @http.route('/zip_product/zip_product/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/zip_product/zip_product/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('zip_product.listing', {
#             'root': '/zip_product/zip_product',
#             'objects': http.request.env['zip_product.zip_product'].search([]),
#         })

#     @http.route('/zip_product/zip_product/objects/<model("zip_product.zip_product"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('zip_product.object', {
#             'object': obj
#         })