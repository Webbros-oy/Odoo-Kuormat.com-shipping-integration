from odoo import api, fields, models

class StockPicking(models.Model):
    """
    Extends stock.picking to support multiple Kuormat shipments and 
    actions for generating labels directly from the transfer.
    """
    _inherit = 'stock.picking'

    wb_kuormat_shipment_ids = fields.One2many('wb.kuormat.shipment', 'picking_id', string='Kuormat Shipments')
    wb_kuormat_show_price = fields.Boolean(related='carrier_id.wb_kuormat_show_price_in_delivery')
    wb_kuormat_is_kuormat = fields.Boolean(compute='_compute_wb_kuormat_is_kuormat')

    @api.depends('carrier_id.delivery_type')
    def _compute_wb_kuormat_is_kuormat(self):
        """
        Computes if the associated delivery carrier's type is 'wb_kuormat'.
        Also searches linked Sale Orders to cover Dropship scenarios.
        """
        for rec in self:
            carrier = rec._wb_kuormat_get_carrier()
            rec.wb_kuormat_is_kuormat = (carrier.delivery_type == 'wb_kuormat') if carrier else False

    def _wb_kuormat_get_carrier(self):
        """ Helper to find the relevant carrier, especially for dropship pickings """
        self.ensure_one()
        carrier = self.carrier_id
        if not carrier and hasattr(self, 'sale_id') and self.sale_id:
            carrier = self.sale_id.carrier_id
            
        if not carrier and self.group_id and hasattr(self.env['sale.order'], 'search'):
            so = self.env['sale.order'].sudo().search([('procurement_group_id', '=', self.group_id.id)], limit=1)
            if so:
                carrier = so.carrier_id
                
        return carrier

    def action_open_kuormat_wizard(self):
        """
        Opens the Kuormat booking wizard prefilled with the picking's current data.
        Returns:
            dict: An ir.actions.act_window dictionary to launch the wizard model.
        """
        self.ensure_one()
        carrier = self._wb_kuormat_get_carrier()
        return {
            'name': 'Book Kuormat Shipment',
            'type': 'ir.actions.act_window',
            'res_model': 'wb.kuormat.book.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
                'default_carrier_id': carrier.id if carrier else False,
            }
        }

    def action_get_kuormat_labels(self):
        """
        Action linked to 'Get Labels' button on the picking view.
        Calls the carrier's wb_kuormat_send_shipping method to fetch labels from Kuormat.
        """
        self.ensure_one()
        if self.carrier_id and getattr(self.carrier_id, 'wb_kuormat_send_shipping', None):
            res = self.carrier_id.wb_kuormat_send_shipping(self)
            self.message_post(body="Labels generated for Kuormat shipments")
            return res
        return False
