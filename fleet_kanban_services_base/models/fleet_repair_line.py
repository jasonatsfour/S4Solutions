# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class FleetRepairLine(models.Model):
    """Fleet Repair Line

    """
    _name = 'fleet.repair.line'
    _description = 'Fleet Repair Line'

    name = fields.Char(string='Description', required=True)
    repair_id = fields.Many2one('fleet.repair', ondelete='cascade',
                                string='Repair Order Reference', index=True)
    type = fields.Selection([
        ('add', 'Add'),
        ('remove', 'Remove')
    ], string='Type', required=True)
    product_id = fields.Many2one(
        'product.product', string='Product', required=True)
    invoiced = fields.Boolean(string='Invoiced', copy=False, readonly=True)
    price_unit = fields.Float(string='Unit Price', required=True,
                              digits='Product Price')
    price_subtotal = fields.Float(string='Subtotal', digits=0,
                                  compute='_compute_price_subtotal')
    tax_id = fields.Many2many(
        'account.tax', 'fleet_repair_operation_line_tax',
        'fleet_repair_operation_line_id', 'tax_id', string='Taxes')
    product_uom_qty = fields.Float(
        string='Quantity', default=1.0,
        digits='Product Unit of Measure', required=True)
    product_uom = fields.Many2one('uom.uom', required=False,
                                  string='Product Unit of Measure')
    location_id = fields.Many2one('stock.location',
                                  string='Source Location', index=True)
    location_dest_id = fields.Many2one('stock.location',
                                       string='Dest. Location', index=True)
    move_id = fields.Many2one('stock.move', string='Inventory Move',
                              copy=False, readonly=True)
    lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', copy=False, readonly=True,
        required=True, help=_(
            'The status of a repair line is set automatically '
            'to the one of the linked repair order.')
    )
    stage = fields.Selection([
        ('progress', 'In Progress'),
        ('marked', 'Marked')
    ], string='Stage', copy=False, default='progress',
        readonly=True, required=True)
    fleet_use = fields.Boolean(
        compute='_compute_fleet_in_use', string="Fleet Use")
    service_request_template_id = fields.Many2one(
        'service.request.template', string='Service Request Template',
        index=True, ondelete='cascade')
    service_request_id = fields.Many2one(
        'vehicle.services', string='Service Request',
        index=True, ondelete='cascade')

    @api.depends('product_id', 'product_id.partial_serialization_id',
                 'product_id.partial_serialization_id.fleet_use')
    def _compute_fleet_in_use(self):
        """Compute: Fleet Usage

        :return: None
        """
        for line in self:
            line.fleet_use = line.product_id.is_product_fleet_use()

    @api.depends('price_unit', 'repair_id', 'product_uom_qty', 'product_id')
    def _compute_price_subtotal(self):
        """

        :return: None
        """
        for rec in self:
            taxes = rec.tax_id.compute_all(
                rec.price_unit,
                rec.repair_id.pricelist_id.currency_id,
                rec.product_uom_qty,
                rec.product_id,
                rec.repair_id.partner_id
            )
            rec.price_subtotal = taxes['total_excluded']

    @api.onchange('type', 'repair_id')
    def onchange_operation_type(self):
        """
        On change of operation type it sets source and destination location of
        repair location warehouse and to invoice field.
        @return: None
        """
        wh = False
        if self.repair_id.x_location:
            wh = self.repair_id.x_location.get_warehouse()
        elif self.service_request_id.x_location:
            wh = self.service_request_id.x_location.get_warehouse()
        if wh:
            if self.type == 'add':
                self.onchange_product_id()
                self.location_id = wh.add_source_location.id
                self.location_dest_id = wh.add_destination_location.id
            elif self.type in ['remove', 'edit']:
                self.price_unit = 0.0
                self.tax_id = False
                self.location_id = wh.remove_source_location.id
                self.location_dest_id = wh.remove_destination_location.id

    @api.onchange('repair_id', 'product_id', 'product_uom_qty')
    def onchange_product_id(self):
        """
        On change of product it sets product quantity, tax account, name,
        uom of product, unit price and price subtotal.
        :return: None
        """
        partner = self.repair_id.partner_id
        pricelist = self.repair_id.pricelist_id
        if not self.product_id or not self.product_uom_qty:
            return
        if self.product_id:
            if partner:
                self.name = self.product_id.with_context(
                    lang=partner.lang
                ).display_name
            else:
                self.name = self.product_id.display_name
            self.product_uom = self.product_id.uom_id.id
        if self.type != 'remove':
            if partner and self.product_id:
                self.tax_id = partner.property_account_position_id.map_tax(
                    self.product_id.taxes_id,
                    self.product_id, partner
                ).ids
            warning = False
            if self.repair_id and not pricelist:
                warning = {
                    'title': _('No Pricelist!'),
                    'message': _(
                        'You have to select a pricelist in the Repair form !'
                        '\n Please set one before choosing a product.')
                }
            else:
                price = pricelist.get_product_price(
                    self.product_id,
                    self.product_uom_qty,
                    partner
                ) if self.repair_id else 0
                if self.repair_id and not price:
                    warning = {
                        'title': _('No valid pricelist line found !'),
                        'message': "%s.\n%s." % (
                            _("Couldn't find a pricelist line matching "
                              "this product and quantity"),
                            _("You have to change either the product,"
                              " the quantity or the pricelist"))
                    }
                self.price_unit = price
            if warning:
                return {'warning': warning}

    def _prepare_repair_line_move_line(self):
        """

        :return:
        """
        return {
            'product_id': self.product_id.id,
            'lot_id': self.lot_id and self.lot_id.id or False,
            'product_uom_qty': 0,  # bypass reservation here
            'product_uom_id': self.product_uom.id,
            'qty_done': self.product_uom_qty,
            'package_id': False,
            'result_package_id': False,
            'flight_hours': self.repair_id.vehicle_id.x_flight_hours,
            'repair_product_id': self.repair_id.vehicle_id.product_id.id,
            'vehicle_number': self.repair_id.vehicle_id.license_plate,
            'owner_id': self.repair_id.partner_id and
                        self.repair_id.partner_id.id or False,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id
        }

    def _prepare_repair_line_move(self):
        """

        :return:
        """
        return {
            'name': self.repair_id.name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.product_uom_qty,
            'product_uom': self.product_uom.id,
            'partner_id': self.repair_id.address_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'reference': self.repair_id.name,
            'move_line_ids': [(0, 0, self._prepare_repair_line_move_line())],
            'fleet_repair_id': self.repair_id.id,
            'origin': self.repair_id.name,
        }

    def _create_repair_move(self):
        """

        :return:
        """
        return self.env['stock.move'].create(self._prepare_repair_line_move())

    def _check_before_done(self):
        """

        :return: None or Raise Error
        :raise: Validation Error
        """
        if self.fleet_use and not self.lot_id:
            raise ValidationError(_(
                "A Lot/Serial number must be provided for %s prior to"
                " marking it Done") % self.product_id.name)

    def action_make_done(self):
        """

        :return:
        """
        move = self.env['stock.move']
        moves = self.env['stock.move']
        for operation in self:
            operation._check_before_done()
            if operation.type in ['add', 'remove']:
                move = operation._create_repair_move()
                moves |= move
                operation.write({
                    'move_id': move.id,
                    'state': 'done',
                    'stage': 'marked'
                })
        if moves:
            moves |= move
            moves._action_done()

    def unlink(self):
        """

        :return:
        :raise: User Error
        """
        if self.filtered(lambda rp: rp.stage == 'marked'):
            raise UserError(_(
                "Error..!! You can not delete this line"
                " as Part has already marked as done."))
        return super(FleetRepairLine, self).unlink()
