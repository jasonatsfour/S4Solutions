# -*- coding: utf-8 -*-
# © 2018-Today Aktiv Software (http://aktivsoftware.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Class inherit for adding some configuration."""

    _inherit = 'res.config.settings'

    internal_transfer_kanban_id = fields.Many2one(
        string="Internal Transfer Type for Kanban",
        related='company_id.internal_transfer_kanban_id', readonly=False)
