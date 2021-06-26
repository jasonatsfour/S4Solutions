from odoo import fields, api, _, models
from odoo.exceptions import UserError


class QualityCheck(models.Model):
    _inherit = "quality.check"
    _order = 'sequence,id'

    sequence = fields.Integer(string="Sequence")
    code = fields.Selection(related='picking_type_id.code', readonly=False)
    operation_id = fields.Many2one(string="Operation", related='workorder_id.operation_id', store=True)
    picking_type_id = fields.Many2one(string="Operation Type", related='workorder_id.picking_type_id', store=True)
    failure_message = fields.Html(related="", string="Failure Message", readonly=False)
    note = fields.Html(related='', readonly=False)
    reason = fields.Html('Cause')
    finished_product_sequence = fields.Float('Finished Product Sequence Number')
    worksheet = fields.Selection([
        ('noupdate', 'Do not update page'),
        ('scroll', 'Scroll to specific page')], string="Worksheet",
        default="noupdate")
    worksheet_page = fields.Integer('Worksheet page')
    operation_edit_allowed = fields.Boolean(string="Operation Edits Allowed",
                                            related="picking_type_id.operation_edit_allowed",
                                            store=True)

    @api.model
    def create(self, vals):
        res = super(QualityCheck, self).create(vals)
        if res.workorder_id:
            res.write({
                'finished_product_sequence': res.workorder_id.qty_produced,
            })
        return res

    def unlink(self):
        res = False
        for rec in self:
            if rec.workorder_id and rec.quality_state != 'none':
                raise UserError("You can not delete any processed quality checks.")
            if len(rec.workorder_id.check_ids) == 1 and not self._context.get('force_delete', False):
                raise UserError("At least one quality check should be there.")
            deleted_rec = rec.id
            workorder = rec.workorder_id
            res = super(QualityCheck, rec).unlink()
            if workorder.current_quality_check_id.id == deleted_rec:
                sorted_quality_checks = workorder.check_ids.filtered(
                    lambda c: c.quality_state == 'none').sorted(lambda l: l.sequence)
                if sorted_quality_checks:
                    workorder.with_context(raise_warning=False).write({'current_quality_check_id': sorted_quality_checks[0].id})
        return res

