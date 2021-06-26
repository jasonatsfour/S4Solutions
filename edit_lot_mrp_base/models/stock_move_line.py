# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class StockMoveLine(models.Model):
    """Move Lines

    Methods:
    update_lot_produced

    ORM:
    write: Mo manage Produced lot to map installed location on serial/lot.
    """
    _inherit = "stock.move.line"

    def write(self, values):
        """ORM: Write



        :param values: Received values in dictionary format
        :return: From super call
        """
        if 'lot_id' in values and self.consume_line_ids:
            self.consume_line_ids.update_lot_produced(
                self.lot_id.id, values['lot_id'])
        res = super(StockMoveLine, self).write(values)
        return res

    def update_lot_produced(self, old_produced_lot, new_produced_lot):
        """Manage Lot Produced.

        To replace old lot with new lot on moves to unlink the older and
        it installation location.

        :param old_produced_lot: Serial/Lot to only unlink not delete
        :param new_produced_lot: Serial/Lot to link
        :return:
        """
        self.write({
            'lot_produced_ids': [
                (3, old_produced_lot),
                (4, new_produced_lot)
            ]
        })
