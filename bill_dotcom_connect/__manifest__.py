# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2016-Present Techspawn Solutions Pvt. Ltd.
# (<https://techspawn.com/>)
#
##########################################################################

{
    'name': 'Odoo Bill.com Connect',
    'version': '13.0',
    'category': 'Accounting',
    'sequence': 1,
    'license': 'OPL-1',
    'currency': 'EUR',
    'author': 'Techspawn Solutions Pvt. Ltd.',
    'website': 'http://www.techspawn.com',
    'description': """

Odoo Bill.com Connect
=========================

This Module will Connect Odoo with Bill.com and synchronise Data.
------------------------------------------------------------------------------


Some of the feature of the module:
--------------------------------------------

  1. Synchronise the products.

  2. Synchronise the products attributes.

  3. Synchronise the Vendors.

  5. Synchronise the Vendor Bills.

----------------------------------------------------------------------------------------------------------
    """,
    'demo_xml': [],
    'update_xml': [],
    'depends': ['base',
                'sh_message',
                'product',
                'website',
                'stock',
                'sale',
                'sale_management',
                # 'website_sale'
                ],
    'data': [
                'security/bridge_security.xml',
                'security/ir.model.access.csv',
                'views/bridge_view.xml',
                'views/customer.xml',
                'views/account_bills.xml',
                'views/product.xml',
                'data/cron.xml'
             ],
    'js': [],
    'application': True,
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
