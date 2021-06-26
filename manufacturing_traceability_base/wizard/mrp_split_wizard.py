# -*- coding: utf-8 -*-
# See LICENSE file for full copyright & licensing details.

from odoo import models, fields, _, api


class MrpSplitWizard(models.TransientModel):
    _name = 'mrp.split.wizard'
    _description = "Mrp Split"

    finished_lot_ids = fields.Many2many('stock.production.lot',
                                        'finished_lot_mrp_split_rel',
                                        'split_id',
                                        'lot_id',
                                        string="Finished Lots", required=True)
    production_id = fields.Many2one('mrp.production', string="Production")
    workorder_id = fields.Many2one('mrp.workorder', string="Workorder")

    # Splitting MO for bad quality lots
    def button_mo_split(self):
        calling_from = self.production_id if self.production_id else self.workorder_id if self.workorder_id else False
        calling_from.check_splits_allowed()
        if calling_from:
            calling_from.button_mo_split(finished_lots=self.finished_lot_ids)
