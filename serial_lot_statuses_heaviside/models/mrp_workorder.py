# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models


class MrpProductionWorkcenterLine(models.Model):
    """Inherited: Work Order.

    """
    _inherit = 'mrp.workorder'

    def action_generate_serial(self):
        """Replaced: Action to generate serial.

        """
        self.ensure_one()
        self.finished_lot_id = self.env['stock.production.lot'].with_context({
            'current_wo': self.id
        }).create({
            'product_id': self.product_id.id,
            'company_id': self.company_id.id,
        })
