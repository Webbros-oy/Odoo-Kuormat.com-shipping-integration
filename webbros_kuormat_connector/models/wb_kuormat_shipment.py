from odoo import api, fields, models

class WbKuormatShipment(models.Model):
    """
    Model representing an actual Kuormat Shipment generated for a transfer (stock.picking).
    Stores tracking IDs, pricing points, and time data retrieved from the Kuormat API.
    """
    _name = 'wb.kuormat.shipment'
    _description = 'Kuormat Actual Shipment'

    picking_id = fields.Many2one('stock.picking', string='Transfer', required=True, ondelete='cascade')
    carrier_id = fields.Many2one('delivery.carrier', string='Carrier Method')
    carrier_name = fields.Char(string='Carrier')
    pickup_id = fields.Char(string='Pickup ID')
    shipment_id = fields.Char(string='Kuormat Shipment ID')
    price = fields.Float(string='Price')
    earliest_date = fields.Datetime(string='Earliest Date')
    free_text = fields.Text(string='Free Text (Note)')
    package_ids = fields.One2many('wb.kuormat.package', 'shipment_id', string='Packages')


class WbKuormatPackage(models.Model):
    """
    Linked packages for Kuormat Shipments containing individual tracking URLs.
    """
    _name = 'wb.kuormat.package'
    _description = 'Kuormat Shipment Package'
    _rec_name = 'pack_id'

    shipment_id = fields.Many2one('wb.kuormat.shipment', string='Shipment', required=True, ondelete='cascade')
    pack_id = fields.Char(string='Package ID')
    url = fields.Char(string='Tracking URL')
