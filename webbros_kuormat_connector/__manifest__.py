# -*- coding: utf-8 -*-
{
    'name': 'Delivery Kuormat',
    'version': '1.5',
    'category': 'Inventory/Delivery',
    'summary': 'Kuormat Delivery Integration',
    'author': 'Webbros',
    'description': """
Delivery Kuormat Connector
==========================
This module serves as an integration for the Kuormat Delivery API.
It extends `delivery.carrier` adding basic methods with webbros standard prefixes.
    """,
    'depends': ['delivery', 'stock'],
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
