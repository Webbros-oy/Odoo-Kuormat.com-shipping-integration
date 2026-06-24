# -*- coding: utf-8 -*-
{
    'name': 'Webbros Kuormat.com shipment integration',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Delivery',
    'summary': 'Kuormat.com shipment booking integration',
    'author':  'Webbros',
    'website': 'https://www.webbros.fi/r/Eyq',
    'images':   ['static/description/icon.png'],


    'description': """
Delivery Kuormat.com Connector
==========================
This module serves as an integration for the Kuormat.com Delivery API.
It extends `delivery.carrier` adding basic methods with webbros standard prefixes.
    """,
#    'depends': ['delivery', 'stock', 'sale_stock', 'purchase_stock', 'stock_dropshipping'],
    'depends': ['delivery', 'stock', 'sale_stock', 'purchase_stock'],

    'data': [
        'security/ir.model.access.csv',
        'data/kuormat_shipment_types_data.xml',
        'views/delivery_carrier_views.xml',
        'views/choose_delivery_carrier_views.xml',
        'views/stock_picking_views.xml',
        'wizard/wb_kuormat_book_wizard_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
