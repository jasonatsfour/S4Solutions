# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models


class MrpWorkorderLine(models.Model):
    """Inherited: MRP Workorder Line

    ORM:
    write
    """
    _inherit = 'mrp.workorder.line'

    def write(self, values):
        """ORM: Write

        QC must be updated if lot_id is changes of completed WO.

        :param values: Received values in dictionary format
        :return: None
        """
        res = super(MrpWorkorderLine, self).write(values)
        if 'lot_id' in values and isinstance(values['lot_id'], int):
            self.check_ids.write({
                'lot_id': values['lot_id']
            })
        return res
