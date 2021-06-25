# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import Warning
from datetime import datetime
from odoo.tools import ustr


class ProductTemplate(models.Model):
    _inherit = "product.template"

    mpn = fields.Char(string='Product MPN')
    sku = fields.Char(string='Product SKU')


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    octopart_price = fields.Float(string='Octopart Price')
    as_of = fields.Datetime(string='As of')
    octopart_status = fields.Char(string='Octopart Status')
    manual_override = fields.Boolean(string='Manual Override')
    is_octopart_vendor = fields.Boolean(related='name.octopart', store=True,
                                        string='Is Octopart Vendor')

    @api.model
    def default_get(self, field_list):
        result = super(SupplierInfo, self).default_get(field_list)
        result.update({'min_qty': 1.0})
        return result

    @api.onchange('product_tmpl_id', 'min_qty', 'name')
    def onchange_product(self):
        if self.product_tmpl_id and self.product_tmpl_id.mpn and self.min_qty \
                and self.name and self.name.octopart:
            try:
                self.update_octopart_price()
            except:
                pass

    def update_details_from_octapart(self):
        octopart = self.env['octopart.configuration'].search(
            [('active', '=', True)], limit=1, order='id desc')
        for obj in self:
            vendor = obj.name
            product = obj.product_tmpl_id
            qty = obj.min_qty
            if obj.is_octopart_vendor and vendor and qty and product or \
                    obj.product_code:
                try:
                    obj.as_of = datetime.now()
                    obj.price = 0.0
                    obj.octopart_price = 0.0
                    obj.octopart_status = 'Not found'
                    octopart_product_details = \
                        octopart.fetch_octopart_api_details(
                            vendor, product, qty, obj)
                    if octopart_product_details and \
                            type(octopart_product_details) == type({}):
                        # if obj.min_qty < octopart_product_details.get('moq'):
                        #     obj.min_qty = octopart_product_details.get('moq')
                        obj.octopart_price = octopart_product_details.get(
                            'price')
                        # obj.price = octopart_product_details.get('price')
                        obj.octopart_status = 'Active'
                    self._cr.commit()
                    return octopart_product_details
                except Exception as e:
                    return e
            else:
                return "Either Octopart is not Enabled in Vendor or missing " \
                       "needed fields details (Vendor / Product / Quantity)"

    def update_octopart_price(self):
        seller_obj = self.env['add.octopart.id']
        api_key = None
        octopart_config = self.env['octopart.configuration'].search([(
            'status', '=', 'Active')], limit=1, order='id desc')
        if octopart_config:
            api_key = octopart_config.api_key
        if not self.name.octopart and not self.name.octopart_id:
            sellers_dict = self.env['fetch.seller.detail'].fetch_detail(
                api_key, '{"sku":"%s"}' % (self.product_code)) or []
            sellers_ids = []
            self.env['add.octopart.id'].search([]).unlink()
            wizard_id = self.env['add.octopart.wizard'].create({})
            for values in sellers_dict:
                values.update({'wizard_id': wizard_id.id, })
                sellers_ids.append(seller_obj.create(values).id)
            self._cr.commit()

            view_id = self.env.ref(
                'odoo_octopart_integration.add_octopart_wizard_view')
            view = {
                'name': _('Update Octopart Vendor Detail'),
                'type': 'ir.actions.act_window',
                'res_model': 'add.octopart.wizard',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'res_id': wizard_id.id,
                'views': [(view_id.id, 'form')],
            }
            return view

        if self.name.octopart:
            octopart_result = self.update_details_from_octapart()
            if octopart_result and type(octopart_result) == type({}):
                raise Warning(_('Pricelist is updated successfully!'))
            else:
                raise Warning(_('Pricelist is not updated. Here is what we '
                                'got instead:\n %s') % ustr(octopart_result))
        else:
            raise Warning(_("Vendor is not an Octopart vendor!"))
