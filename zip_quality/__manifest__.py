# -*- coding: utf-8 -*-
{
    'name': "Zipline Quality Template",
    'summary': "Custom extensions to the Product record for Zipline",
    'description': "Adds in additional data elements from Aras.",
    'author': "Zipline International",
    'website': "http://www.flyzipline.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Quality',
    'version': '0.0.1',
    'license': 'Other proprietary',
 
    # any module necessary for this one to work correctly
    'depends': ['product', 'stock', 'purchase'],
    
    # always loaded
    'data': [
    'views/views.xml',
    'views/location_view.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,    
}
