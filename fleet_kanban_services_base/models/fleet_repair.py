# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError


class FleetRepair(models.Model):
    """Fleet Repair Management.

    """
    _name = 'fleet.repair'
    _description = 'Repair Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _default_stock_location(self):
        """

        :return:
        """
        warehouse = self.env['stock.warehouse'].search([], limit=1)
        if warehouse:
            return warehouse.lot_stock_id.id
        return False

    name = fields.Char(string='Reference', copy=False, required=True,
                       default=lambda self: _('New'), readonly=True)
    user_id = fields.Many2one(
        'res.users', string='Responsible',
        default=lambda self: self.env.user, track_visibility='onchange')
    type_id = fields.Many2one(
        'fleet.repair.type', string='Type', track_visibility='onchange')
    stage_id = fields.Many2one(
        'fleet.repair.stage', string='Stage', ondelete='restrict', copy=False,
        group_expand='_read_group_stage_ids', track_visibility='onchange')
    is_draft = fields.Boolean(related="stage_id.is_draft")
    in_work = fields.Boolean(related="stage_id.in_work")
    final_stage = fields.Boolean(related="stage_id.final_stage")
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.user.company_id)
    tag_ids = fields.Many2many('fleet.repair.tag', string='Tags')
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'High')
    ], string='Grounding Status', track_visibility='onchange', index=True)
    note = fields.Text(string='Note', copy=False)
    approval_ids = fields.One2many(
        'fleet.repair.approval', 'repair_id', copy=False,
        string='Approvals', help='Approvals by stage')
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('cancel', 'Cancelled'),
        ('confirmed', 'Confirmed'),
        ('under_repair', 'Under Repair'),
        ('ready', 'Ready to Repair'),
        ('2binvoiced', 'To be Invoiced'),
        ('invoice_except', 'Invoice Exception'),
        ('done', 'Repaired')
    ], string='Status', copy=False, default='draft', readonly=True,
        track_visibility='onchange',
        help=_(
            "* The \'Draft\' status is used when a user is encoding a new and"
            " unconfirmed repair order.\n * The \'Confirmed\' status is used "
            "when a user confirms the repair order.\n * The \'Ready to "
            "Repair\' status is used to start to repairing, user can start "
            "repairing only after repair order is confirmed.\n"
            "* The \'To be Invoiced\' status is used to generate the invoice "
            "before or after repairing done.\n * The \'Done\' status is set "
            "when repairing is completed.\n * The \'Cancelled\' status is "
            "used when user cancel repair order.")
    )
    user_can_approve = fields.Boolean(
        string='Can Approve', compute='_compute_user_can_approve',
        help=_(
            'Technical field to check if approval by current user is required'
        ))
    user_can_reject = fields.Boolean(
        string='Can Reject', compute='_compute_user_can_reject',
        help=_(
            'Technical field to check if reject by current user is possible'
        ))
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    x_serial_no = fields.Char(string="Serial #")
    active = fields.Boolean(
        string='Active', default=True,
        help=_('If the active field is set to False, it will allow you '
               'to hide the engineering change order without removing it.')
    )
    vehicle_services_ids = fields.One2many(
        'fleet.repair.service', 'repair_id', copy=False, string='Services')
    kanban_state = fields.Selection([
        ('normal', 'In Progress'),
        ('done', 'Approved'),
        ('blocked', 'Blocked')
    ], string='Kanban State', copy=False,
        compute='_compute_kanban_state', store=True)
    allow_change_stage = fields.Boolean(
        string='Allow Change Stage', compute='_compute_allow_change_stage')
    allow_apply_change = fields.Boolean(
        string='Show Apply Change', compute='_compute_allow_apply_change')
    included_services_ids = fields.One2many(
        'fleet.vehicle.cost', 'repair_id',
        copy=False, string='Included Services')
    operations = fields.One2many('fleet.repair.line', 'repair_id',
                                 string='Parts', copy=False)
    product_id = fields.Many2one(
        'product.product', string='Product to Repair',
        related='vehicle_id.product_id')
    pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist',
        default=lambda self: self.env['product.pricelist'].search(
            [], limit=1).id,
        help='Pricelist of the selected partner.')
    partner_id = fields.Many2one(
        'res.partner', string='Customer', index=True,
        help=_('Choose partner for whom the order '
               'will be invoiced and delivered.'))
    address_id = fields.Many2one(
        'res.partner', string='Delivery Address',
        domain="[('parent_id','=',partner_id)]")
    default_address_id = fields.Many2one(
        'res.partner', compute='_compute_default_address_id')
    repaired = fields.Boolean(string='Repaired', copy=False, readonly=True)
    marked = fields.Boolean(string='Marked', default=False,
                            compute='_compute_marked_operations')
    x_location = fields.Many2one("stock.location", string="Location")

    @api.onchange('x_location')
    def onchange_x_location(self):
        """Onchange: X Location.

        Location is used to set the source & destination for the part.

        :return: None
        """
        if self.x_location and self.operations:
            for part in self.operations:
                part.onchange_operation_type()

    @api.onchange('vehicle_id')
    def onchange_vehicle_id(self):
        """Onchange: Vehicle

        Set vehicle location to repair location to manage the operation source
        and destination locations.

        :return: None
        """
        for repair_order in self:
            repair_order.x_serial_no = repair_order.vehicle_id.x_serial_no
            repair_order.x_location = repair_order.vehicle_id.x_location.id

    @api.depends('partner_id')
    def _compute_default_address_id(self):
        """

        :return: None
        """
        if self.partner_id:
            self.default_address_id = self.partner_id.address_get(
                ['contact'])['contact']

    @api.depends('operations')
    def _compute_marked_operations(self):
        """To check operations marked status.

        For hide the mark all done when all operations are done.

        :return: None
        """
        marked = self.operations.filtered(lambda x: x.stage == 'progress')
        self.marked = False if marked else True

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """

        Read group customization in order to display all the stages of
        the Repair type in the Kanban view.
        Even if there is no Repair in that stage.

        :param stages:
        :param domain:
        :param order:
        :return:
        """
        return stages.browse(stages._search(
            [], order=order, access_rights_uid=SUPERUSER_ID))

    @api.model
    def default_get(self, fields):
        """

        :param fields:
        :return:
        """
        res = super(FleetRepair, self).default_get(fields)
        draft_stage = self.env['fleet.repair.stage'].search([
            ('is_draft', '=', True)
        ], limit=1)
        if draft_stage:
            res.update({'stage_id': draft_stage.id})
        vehicle_id = self._context.get('default_vehicle_id', False)
        if self._context.get('vehicle_services_id', False) and vehicle_id:
            vehicle_service = self.env['vehicle.services'].browse(
                self._context['vehicle_services_id'])
            included_services_ids = []
            for included_service in vehicle_service.included_services_ids:
                included_services_ids += [(0, 0, {
                    'cost_subtype_id': included_service.cost_subtype_id.id,
                    'amount': included_service.amount,
                    'vehicle_id': vehicle_id
                })]
            res.update({
                'included_services_ids': included_services_ids,
                'vehicle_services_ids': [(0, 0, {
                    'service_id': vehicle_service.id
                })]
            })
        return res

    @api.onchange('stage_id')
    def onchange_stage_id(self):
        """Onchange Stage

        When RO going to done/final stage it check that is any Operation is in
        pending state or not, If any then it will raise an user error.

        Error: All Vehicle Services related to this RO are still in Pending.
        You cannot Complete this Repair Order.
        Please complete all services first.

        :return: None or Raise User Error
        :raise: User Error
        """
        vehicle_services_ids = self.env['fleet.repair.service'].search([
            ('repair_id', 'in', self._origin.ids)
        ])
        final_statge = self.env['vehicle.service.state'].search([
            ('final_stage', '=', True)
        ], limit=1)
        moc = self.env['fleet.vehicle.available'].search([
            ('moc', '=', True)
        ], limit=1)

        for repair in self:
            service_completed = repair.operations.filtered(
                lambda line: line.stage == 'marked'
            )
            if repair.final_stage and \
                    len(service_completed) != len(repair.operations.ids):
                raise UserError(_(
                    "All Vehicle Services related to this Repair Order are "
                    "still in Pending State.\n You cannot Complete this "
                    "Repair Order. Please complete all services first."
                ))

            # if record move to completed stage from any stage
            if repair.stage_id.final_stage:
                vehicle_services_ids.filtered(
                    lambda ro: ro.repair_id == repair
                ).mapped('service_id').write({
                    'stage_id': final_statge.id
                })
            elif repair.stage_id.moc:
                if not vehicle_services_ids.filtered(
                        lambda line: line.repair_id == repair and not
                        line.service_id.stage_id.final_stage and
                        line.service_id.priority == 'critical' and
                        line.service_id.critical_selection == 'yes'):
                    repair.vehicle_id.x_availability = moc.id

    @api.depends('approval_ids')
    def _compute_user_can_approve(self):
        """

        :return:
        """
        approvals = self.env['fleet.repair.approval'].search([
            ('repair_id', 'in', self.ids),
            ('status', 'not in', ['approved']),
            ('template_stage_id', 'in', self.mapped('stage_id').ids),
            ('approval_template_id.approval_type', 'in',
             ('mandatory', 'optional')),
            ('required_user_ids', 'in', self.env.uid)])
        to_approve_repair_ids = approvals.mapped('repair_id').ids
        for repair in self:
            repair.user_can_approve = repair.id in to_approve_repair_ids

    @api.depends('stage_id', 'approval_ids.is_approved',
                 'approval_ids.is_rejected')
    def _compute_kanban_state(self):
        """

        State of ECO is based on the state of approvals for the current stage.

        :return:
        """
        approvals = self.approval_ids.filtered(
            lambda app: app.template_stage_id == self.stage_id)
        if not approvals:
            self.kanban_state = 'normal'
        elif all(approval.is_approved for approval in approvals):
            self.kanban_state = 'done'
        elif any(approval.is_rejected for approval in approvals):
            self.kanban_state = 'blocked'
        else:
            self.kanban_state = 'normal'

    @api.depends('kanban_state', 'stage_id', 'approval_ids')
    def _compute_allow_change_stage(self):
        """

        :return:
        """
        approvals = self.approval_ids.filtered(
            lambda app: app.template_stage_id == self.stage_id)
        if approvals:
            self.allow_change_stage = self.kanban_state == 'done'
        else:
            self.allow_change_stage = self.kanban_state in ['normal', 'done']

    @api.depends('state', 'stage_id.allow_apply_change')
    def _compute_allow_apply_change(self):
        """

        :return:
        """
        self.allow_apply_change = self.state in (
            'confirmed', 'progress') and self.stage_id.allow_apply_change

    @api.depends('approval_ids')
    def _compute_user_can_reject(self):
        """

        :return:
        """
        approvals = self.env['fleet.repair.approval'].search([
            ('repair_id', 'in', self.ids),
            ('status', 'not in', ['rejected']),
            ('template_stage_id', 'in', self.mapped('stage_id').ids),
            ('approval_template_id.approval_type', 'in',
             ('mandatory', 'optional')),
            ('required_user_ids', 'in', self.env.uid)])
        to_reject_repair_ids = approvals.mapped('repair_id').ids
        for repair in self:
            repair.user_can_reject = repair.id in to_reject_repair_ids

    def _create_approvals(self):
        """

        :return:
        """
        rp_approve = self.env['fleet.repair.approval']
        for repair in self:
            for approval_template in repair.stage_id.approval_template_ids:
                approval = repair.approval_ids.filtered(
                    lambda app: app.approval_template_id == approval_template)
                if not approval:
                    rp_approve.create({
                        'repair_id': repair.id,
                        'approval_template_id': approval_template.id
                    })
                # If approval already exists update it
                else:
                    if approval.status != 'none':
                        msg = 'Approval: %s was %s' % (
                            approval.name, approval.status)
                        if approval.user_id:
                            msg = msg + ' by ' + approval.user_id.name
                        msg += '.'
                        repair.message_post(body=msg)
                        approval.write({
                            'status': 'none',
                            'user_id': False,
                        })

    def _get_repair_approvals(self):
        """

        :return:
        """
        return self.approval_ids.filtered(
            lambda app:
            app.template_stage_id == self.stage_id and
            app.approval_template_id.approval_type in
            ('mandatory', 'optional') and
            self.env.user in app.approval_template_id.user_ids
        )

    def _update_approval_state(self, state):
        """

        :param state: 
        :return: 
        """
        approvals = self._get_repair_approvals()
        if approvals:
            approvals.write({
                'status': state,
                'user_id': self.env.uid
            })

    def button_approve_reject(self, state):
        """

        :return:
        """
        for repair in self:
            repair._update_approval_state(state)

    def approve(self):
        """

        :return:
        """
        self.button_approve_reject(state='approved')

    def reject(self):
        """

        :return:
        """
        self.button_approve_reject(state='rejected')

    @api.model
    def create(self, vals):
        """
        Override Create Method to add vehicle repair order sequence and
        to create approvals.
        :param vals:
        :return:
        """
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'fleet.repair') or _('New')
        if self._context.get('vehicle_services_id', False):
            vals['vehicle_services_ids'] = [(0, 0, {
                'service_id': self._context['vehicle_services_id']
            })]
        res = super(FleetRepair, self).create(vals)
        if vals.get('stage_id'):
            self._create_approvals()
        return res

    def write(self, vals):
        """ORM: Write.

        Method to create approvals.

        :param vals:
        :return: None or User Error
        :raise: User Error
        """
        if 'stage_id' in vals:
            rp_stage = self.env['fleet.repair.stage']
            new_stage = rp_stage.browse(vals['stage_id'])
            # raise exception only if we increase the stage, not on decrease
            if self.stage_id and ((new_stage.sequence, new_stage.id) > (
                    self.stage_id.sequence, self.stage_id.id)):
                if any(not repair.allow_change_stage for repair in self):
                    raise UserError(_(
                        'You cannot change the stage, '
                        'as approvals are still required.'
                    ))
                minimal_sequence = min(
                    self.mapped('stage_id').mapped('sequence'))
                has_blocking_stages = rp_stage.search_count([
                    ('sequence', '>=', minimal_sequence),
                    ('sequence', '<=', new_stage.sequence),
                    ('type_id', 'in', self.mapped('type_id').ids),
                    ('id', 'not in', self.mapped('stage_id').ids + [
                        vals['stage_id']]),
                    ('is_blocking', '=', True)
                ])
                if has_blocking_stages:
                    raise UserError(_(
                        'You cannot change the stage, as '
                        'approvals are required in the process.'))
            if new_stage.final_stage:
                if self.included_services_ids.filtered(
                        lambda line: line.cost_subtype_id.moc and not
                        line.x_completed_by):
                    self.message_post(
                        '<p style="color:red;font-weight:bold"> Repair Order '
                        'completed without all MOCs having been signed off at '
                        'the time of its completion. </p>')
        res = super(FleetRepair, self).write(vals)
        if vals.get('stage_id'):
            self._create_approvals()
        return res

    @api.model
    def get_repair_order_rec(self, vehicle_services):
        """

        :param vehicle_services:
        :return:
        """
        vehicle_services_rec = self.env['vehicle.services'].search([
            ('id', '=', vehicle_services)
        ])
        repairs_order_rec = [repair for repair in self.search([
            ('vehicle_id', '=', vehicle_services_rec.vehicle_id.id)
        ]) if repair]
        if not repairs_order_rec:
            return False
        repair_list = []
        for repair_order in repairs_order_rec:
            model = repair_order.vehicle_id.model_id
            repair_list.append({
                'reference': repair_order.name,
                'responsible': repair_order.user_id.name,
                'vehicle_services': vehicle_services_rec.id,
                'vehicle_model': model.name,
                'vehicle_brand': model.brand_id.name,
            })
        return repair_list

    @api.model
    def add_vehicle_service(self, fleet_repair_details, vehicle_service_rec):
        """

        :param fleet_repair_details:
        :param vehicle_service_rec:
        :return:
        """
        if fleet_repair_details:
            for repair_detail in eval(fleet_repair_details):
                if repair_detail.get('0'):
                    fleet_repair_id = self.search([
                        ('name', 'ilike', repair_detail.get('0'))
                    ])
                    fleet_repair_id.write({
                        'vehicle_services_ids': [(0, 0, {
                            'service_id': vehicle_service_rec
                        })]
                    })

    def action_repair_confirm(self):
        """

        :return:
        """
        to_confirm_operations = self.mapped('operations')
        if to_confirm_operations:
            to_confirm_operations.write({'state': 'confirmed'})
        self.write({'state': 'confirmed'})
        return True

    def _check_repair_product(self):
        """Check Repair Product

        Repair must have the Vehicle product, if it not the RAISE Error.
        Error: Please specify Repair Product for Vehicle.

        :return: None or RAISE Validation Error
        :raise: Validation Error
        """
        if not self.vehicle_id.product_id and not self.product_id:
            raise ValidationError('%s %s.' % (
                _('Please specify Repair Product for'),
                self.vehicle_id.name
            ))

    def action_make_all_done(self):
        """Action Make All Done
        Creates stock move for all operation of repair order.
        :return: True
        """
        for repair in self:
            repair._check_repair_product()
            repair.operations.action_make_done()
        return True
