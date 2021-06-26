# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import models


class Repair(models.Model):
    """Inherited: Repair Order

    """
    _inherit = 'repair.order'

    def action_repair_end(self):
        """Inherited: Action Repair End

        Writes repair order state to 'To be invoiced' if invoice method is
        After repair else state is set to 'Ready'.
        Also set production id in stock move lines to map in report.

        :return: True
        """
        res = super(Repair, self).action_repair_end()
        move_line = self.env['stock.move.line']
        for repair in self:
            line_id = move_line.search([
                ('state', '=', 'done'),
                ('product_id', '=', repair.product_id.id),
                ('lot_id', '=', repair.lot_id.id if repair.lot_id else False),
                ('move_id.production_id', '!=', False)
            ], limit=1)
            done_line = self.env['traceability.mark.done']
            if line_id and line_id.move_id.production_id:
                production_id = line_id.move_id.production_id

                check_line_exist = done_line.search([
                    ('production_id', '=', production_id.id),
                ], order='id DESC', limit=1)

                if not check_line_exist:
                    search_old_moves = move_line.search([
                        '|', ('reference', '=', production_id.name),
                        ('production_id', '=', production_id.id)
                    ])
                    trace_log_old_mv = done_line
                    for old_mv in search_old_moves:
                        old_repair = old_mv.move_id.repair_id or False
                        old_repair_type = 'add'
                        if old_mv.move_id and old_repair:
                            old_repair_type = old_repair.operations.filtered(
                                lambda o: o.product_id == old_mv.product_id
                                          and o.lot_id == old_mv.lot_id
                            ).type
                            old_repair = old_mv.move_id.repair_id.id
                        old_lot = old_mv.lot_id.id if old_mv.lot_id else False
                        new_track = {
                            'production_id': production_id.id,
                            'repair_id': old_repair,
                            'product_id': old_mv.product_id.id,
                            'move_line_id': old_mv.id,
                            'lot_id': old_lot,
                            'qty_done': old_mv.qty_done,
                            'reference': old_mv.reference,
                            'operation_type': old_repair_type
                        }
                        res = done_line.create(new_track)
                        trace_log_old_mv |= res
                        if old_repair_type == 'remove':
                            last_add_move = trace_log_old_mv.filtered(
                                lambda t:
                                t.operation_type == 'add' and
                                t.product_id == res.product_id and
                                t.lot_id == res.lot_id and
                                t.qty_done != 0
                            )
                            last_add_move[0].qty_done -= res.qty_done
                all_repair_lines = repair.operations.filtered(
                    lambda o: o.type == 'add'
                ).mapped('move_id').mapped('move_line_ids')

                for line in all_repair_lines:
                    new_track = {
                        'production_id': production_id.id,
                        'repair_id': repair.id,
                        'product_id': line.product_id.id,
                        'move_line_id': line.id,
                        'lot_id': line.lot_id.id if line.lot_id else False,
                        'qty_done': line.qty_done,
                        'reference': line.reference,
                        'operation_type': 'add'
                    }
                    done_line.create(new_track)
                all_repair_lines = repair.operations.filtered(
                    lambda o: o.type == 'remove'
                ).mapped('move_id').mapped('move_line_ids')

                for line in all_repair_lines:
                    searched_line = done_line.search([
                        ('product_id', '=', line.product_id.id),
                        ('lot_id', '=',
                         line.lot_id.id if line.lot_id else False),
                        ('production_id', '=', production_id.id),
                        ('qty_done', '>', 0),
                        ('operation_type', '=', 'add')
                    ], order='id DESC', limit=1)
                    searched_line.qty_done -= line.qty_done
                    new_track = {
                        'production_id': production_id.id,
                        'repair_id': repair.id,
                        'product_id': line.product_id.id,
                        'move_line_id': line.id,
                        'lot_id': line.lot_id.id if line.lot_id else False,
                        'qty_done': line.qty_done,
                        'reference': line.reference,
                        'operation_type': 'remove'
                    }
                    done_line.create(new_track)

                lines = move_line.search([
                    ('reference', '=', repair.name),
                    ('state', '=', 'done'),
                    ('product_id', '!=', repair.product_id.id),
                ])
                lines.mapped('move_id').write({
                    'production_id': production_id.id
                })
                lines.write({
                    'production_id': production_id.id
                })
        return res
