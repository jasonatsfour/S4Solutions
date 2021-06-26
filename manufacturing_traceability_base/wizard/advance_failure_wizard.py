# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import UserError


class MessageWizard(models.TransientModel):
    """
        return: custom message wizard
        custom: only you need to write logic for on confirm what you want to call?
    """
    _name = 'message.wizard'

    name = fields.Text()
    workorder_id = fields.Many2one('mrp.workorder', string="Workorder")
    workorder_ids = fields.Many2many('mrp.workorder', 'mrp_workorder_ids_rel_table',
                                     'wizard_id', 'workorder_id', string="Workorder")
    condition_name = fields.Char(string="Which condition checked?")
    stock_move_ids = fields.Many2many('stock.move', 'message_wizard_stock_move_rel',
                                      'wizard_id', 'move_id', string="Move")

    def confirm(self):
        if self.workorder_ids:
            if self.condition_name == 'progress_condition_checked':
                action, last_workorder = self.workorder_ids.checking_preconditions_for_deleting_work_orders(
                    progress_condition_checked=True)
                return action
            elif self.condition_name == 'check_ids_condition_checked':
                action, last_workorder = self.workorder_ids.checking_preconditions_for_deleting_work_orders(
                    progress_condition_checked=True, check_ids_condition_checked=True)
                return action
            else:
                raise UserError("something went wrong.")
        elif self.stock_move_ids:
            self.stock_move_ids.action_reverse_moves(
                for_mo=True,
                reference=self.stock_move_ids[0].raw_material_production_id.name
                or self.stock_move_ids[0].production_id.name
            )
        else:
            self.workorder_id.production_id.button_mo_split(self.workorder_id.finished_lot_id, remove_assembly=True)


class AdvanceFailureFeature(models.TransientModel):
    """

    """
    _name = 'advance.failure.popup.wizard'

    workorder_id = fields.Many2one('mrp.workorder', string="Workorder")
    production_id = fields.Many2one('mrp.production', string="Production", related="workorder_id.production_id")
    current_quality_check_id = fields.Many2one('quality.check',
                                               related="workorder_id.current_quality_check_id",
                                               string="Current Quality Check")

    def button_re_test(self):
        self.workorder_id.create_re_testable_check()
        self.current_quality_check_id.write({'quality_state': 'none'})
        return True

    def button_continue_with_failure(self):
        self.current_quality_check_id.do_fail()
        return self.workorder_id._next()

    def button_remove_assembly(self):
        return {
            'name': 'Confirmation',
            'type': 'ir.actions.act_window',
            'res_model': 'message.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_name': '[{0}] is going to be removed from '
                                        'this Manufacturing Order. Are you sure you want to continue?'.format(
                self.workorder_id.finished_lot_id.name), 'default_workorder_id': self.workorder_id.id}
        }
