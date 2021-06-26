# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID, _

class AsBuildReport(models.Model):
    _name = 'as.build.report'


    def _default_mo_ids(self):
        mo_list = []
        mo_ids = self._context.get('active_model') == 'mrp.production' and self._context.get('active_ids') or []
        for mo in self.env['mrp.production'].browse(mo_ids):
            if mo.state in ['done']:
                mo_list.append(mo.id)
        return mo_list
        
    manufacture_ids = fields.One2many('mrp.production','manufacture_id','MO Orders',default=_default_mo_ids)
    mo_ids = fields.Many2many('mrp.production')

    
    def action_repair_order(self):
        mo_ids = self._context.get('active_model') == 'mrp.production' and self._context.get('active_ids') or []
        for mo in mo_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'stock_report_generic',
                'context': {'url': '/stock/output_format/stock/1', 'model': 'stock.traceability.report'},
            }
