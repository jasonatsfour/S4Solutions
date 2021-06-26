# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ZipQuality(models.Model):
    _inherit = "product.template"

    x_aql = fields.Char('AQL')
    x_ip = fields.Char('Inspection Plan')
    x_time = fields.Float('Time to Insepct a Part')
    
class QualityLocation(models.Model):
	_inherit = "stock.location"

	x_preinspection = fields.Boolean('Pre Inspection Location')