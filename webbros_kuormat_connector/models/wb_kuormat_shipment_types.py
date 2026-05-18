from odoo import api, fields, models

class WbKuormatShipmentTypes(models.Model):
    """
    Model defining the package types supported by Kuormat (e.g., parcel, half_pallet).
    Includes default dimensions required for API requests.
    """
    _name = 'wb.kuormat.shipment.types'
    _description = 'Kuormat Shipment Types'

    name = fields.Char(string='Name', required=True)
    default_length = fields.Integer(string='Default Length (cm)')
    default_width = fields.Integer(string='Default Width (cm)')
    default_height = fields.Integer(string='Default Height (cm)')
