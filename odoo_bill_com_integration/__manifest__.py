# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2016-Present Techspawn Solutions Pvt. Ltd.
# (<https://techspawn.com/>)
#
##########################################################################

{
    'name': 'Odoo Bill.com Integration',
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

  1. Import bills, chart of accounts and vendors in odoo.


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
                'account',
                # 'website_sale'
                ],
    'data': [
                'security/bridge_security.xml',
                'security/ir.model.access.csv',
                'views/bridge_view.xml',
                'views/vendor.xml',
                'views/account.xml',
                'views/bill.xml',
                'views/cron.xml',
             ],
    'js': [],
    'application': True,
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
