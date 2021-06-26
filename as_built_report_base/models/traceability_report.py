# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import api, models

rec = 0


# Function for get Id
def auto_increment():
    """Unique ID for Lines.

    Return sequential unique id with global variable rec.

    :return: Integer
    """
    global rec
    p_start = 1
    p_interval = 1
    if rec == 0:
        rec = p_start
    else:
        rec += p_interval
    return rec


class MrpStockReport(models.TransientModel):
    """Inherited: MRP Stock Report

    """
    _inherit = 'stock.traceability.report'

    @api.model
    def _get_linked_move_lines(self, move_line):
        """Inherited: Linked Move lines.

        :param move_line: Move lines to display
        :return: Lines and Is used flag
        """
        move_lines, is_used = super(
            MrpStockReport, self)._get_linked_move_lines(move_line)
        trace_done = self.env['traceability.mark.done']
        if move_lines:
            move_ids = move_lines.mapped('move_id')
            for move_id in move_ids:
                move_lines |= move_id.move_line_ids
        if self._context.get('model', '') == 'mrp.production':
            production_id = self.env['mrp.production'].browse(
                self._context['active_id'])
            repair_move_lines = trace_done.search([
                ('production_id', '=', production_id.id),
                ('operation_type', '=', 'add')
            ])
            if repair_move_lines and move_lines:
                move_lines |= repair_move_lines.mapped('move_line_id')
        elif move_line.location_id.usage == 'production':
            repair_move_lines = trace_done.search([
                ('move_line_id', '=', move_line.id),
                ('operation_type', '=', 'add')
            ]).production_id
            repair_move_lines = trace_done.search([
                ('production_id', '=', repair_move_lines.id),
                ('move_line_id', '!=', move_line.id),
                ('operation_type', '=', 'add')
            ])
            if repair_move_lines and move_lines:
                removed_ro = repair_move_lines.filtered(
                    lambda r: r.qty_done < 1).mapped('move_line_id').ids
                move_lines |= repair_move_lines.mapped('move_line_id')
                move_lines = move_lines.filtered(
                    lambda m: m.id not in removed_ro)
        move_lines = move_lines.filtered(lambda x: x.qty_done > 0)
        return move_lines, is_used

    def prepare_final_vals_to_lines(self, data, level, qty_uom):
        """Prepare Lines to render on Report screen.

        :param data: Dictionary
        :param level: Integer
        :param qty_uom: UoM
        :return: Dictionary
        """
        vals = {
            'id': auto_increment(),
            'model': data['model'],
            'model_id': data['model_id'],
            'parent_id': data['parent_id'],
            'usage': data.get('usage', False),
            'is_used': data.get('is_used', False),
            'lot_name': data.get('lot_name', False),
            'lot_id': data.get('lot_id', False),
            'product': data.get('product_id', False),
            'reference': data.get('reference_id', False),
            'res_id': data.get('res_id', False),
            'res_model': data.get('res_model', False),
            'level': level,
            'unfoldable': data['unfoldable'],
        }
        # add condition for remove duplication of product name.
        if data.get('res_model') == 'stock.inventory':
            vals.update({
                'inventory_adj': True,
                # Update column sequence
                'columns': [
                    data.get('', False),
                    data.get('reference_id', False),
                    data.get('lot_name', False),
                    qty_uom,
                    data.get('location_source', False),
                    data.get('location_destination', False),
                    data.get('date', False)
                ],
            })
        else:
            vals.update({
                # Update column sequence
                'columns': [
                    data.get('product_id', False),
                    data.get('reference_id', False),
                    data.get('lot_name', False),
                    qty_uom,
                    data.get('location_source', False),
                    data.get('location_destination', False),
                    data.get('date', False)
                ],
            })
        return vals

    @api.model
    def _final_vals_to_lines(self, final_vals, level):
        """Overwrite: Final Lines.

        Function Inherit for Update column sequence.

        :param final_vals: List of Dictionaries
        :param level: Integer
        :return: List of Dictionaries
        """
        lines = []
        trc_mark_done_env = self.env['traceability.mark.done']
        for data in final_vals:
            domain = [
                ('production_id', '=', data.get('res_id')),
                ('operation_type', '=', 'remove'),
            ]
            if data.get('lot_id'):
                domain.append(('lot_id', '=', data.get('lot_id')))
            else:
                data_product_name = data.get('product_id')
                if '] ' in data_product_name:
                    domain.append(
                        ('product_id.name', '=',
                         data_product_name.split('] ')[1])
                    )
                else:
                    domain.append(
                        ('product_id.name', '=', data_product_name)
                    )
            trace_removed = trc_mark_done_env.search(domain)
            qty_uom = data.get('product_qty_uom', 0)
            if trace_removed:
                qty_uom = qty_uom.split(' ')
                qty_part = float(qty_uom[0]) - sum(
                    trace_removed.mapped('qty_done'))
                if not qty_part:
                    continue
                qty_uom = '%.3f %s' % (qty_part, qty_uom[1])
            lines.append(
                self.prepare_final_vals_to_lines(data, level, qty_uom)
            )
        return lines

    @api.model
    def get_lines(self, line_id=None, **kw):
        """Overwrite: Lines of current move.

        :param line_id: Move line ID (Integer)
        :param kw: KW Args
        :return: List of Dictionaries
        """
        ctx = dict(self.env.context)
        model = kw.get('model_name', ctx.get('model'))
        rec_id = kw.get('model_id', ctx.get('active_id'))
        level = kw.get('level', 1)
        lines = self.env['stock.move.line']
        move_line = self.env['traceability.mark.done']
        if rec_id and model == 'stock.production.lot':
            lines = move_line.search([
                ('lot_id', '=', ctx.get('lot_name') or rec_id),
                ('move_line_id.state', '=', 'done'),
                ('operation_type', '=', 'add')
            ]).mapped('move_line_id')
        elif rec_id and model == 'stock.move.line' and ctx.get('lot_name'):
            record = self.env[model].browse(rec_id)
            # if not record.move_id.scrapped:
            dummy, is_used = self._get_linked_move_lines(record)
            if is_used:
                lines = is_used
        elif rec_id and model in ('stock.picking', 'mrp.production'):
            record = self.env[model].browse(rec_id)
            if model == 'stock.picking':
                lines = record.move_lines.mapped('move_line_ids').filtered(
                    lambda m: m.lot_id and m.state == 'done')
            else:
                lines = record.move_finished_ids.filtered(
                    lambda m: not m.repair_id
                ).mapped('move_line_ids').filtered(
                    lambda m: m.state == 'done')
        move_line_vals = self._lines(line_id, model_id=rec_id, model=model,
                                     level=level, move_lines=lines)
        final_vals = sorted(move_line_vals,
                            key=lambda v: v['date'], reverse=True)
        return self._final_vals_to_lines(final_vals, level)
