from odoo import fields, api, _, models


class QualityPoint(models.Model):
	_inherit = "quality.point"

	def coming_from_workorder(self):
		from_workorder, product_id, operation_id, picking_type_id = self._context.get(
			'from_workorder'), self._context.get('default_product_id'), self._context.get(
			'default_operation_id'), self._context.get('default_picking_type_id')
		return (from_workorder, product_id, operation_id, picking_type_id) \
			if from_workorder else (False, False, False, False)

	@api.model
	def default_get(self, default_fields):
		res = super(QualityPoint, self).default_get(default_fields)
		(from_workorder, product_id, operation_id, picking_type_id) = self.coming_from_workorder()
		if from_workorder:
			res.update({
				'product_tmpl_id': self.env['product.product'].browse(product_id).product_tmpl_id.id
			})
		return res

	@api.model
	def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
		domain = []
		(from_workorder, product_id, operation_id, picking_type_id) = self.coming_from_workorder()
		if from_workorder:
			args.append(('product_id', '=', product_id))
			args.append(('operation_id', '=', operation_id))
			args.append(('picking_type_id', '=', picking_type_id))
		args += domain
		return super(QualityPoint, self)._search(
			args, offset, limit, order, count=count, access_rights_uid=access_rights_uid)
