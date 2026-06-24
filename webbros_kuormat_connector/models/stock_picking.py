from odoo import api, fields, models, _
from lxml import html

class StockPicking(models.Model):
    """
    Extends stock.picking to support multiple Kuormat shipments and
    actions for generating labels directly from the transfer.
    """
    _inherit = 'stock.picking'

    wb_kuormat_shipment_ids = fields.One2many('wb.kuormat.shipment', 'picking_id', string='Kuormat Shipments')
    wb_kuormat_show_price = fields.Boolean(compute='_compute_wb_kuormat_show_price')
    wb_kuormat_is_kuormat = fields.Boolean(compute='_compute_wb_kuormat_is_kuormat')

    @api.depends('carrier_id.wb_kuormat_show_price_in_delivery')
    def _compute_wb_kuormat_show_price(self):
        for rec in self:
            carrier = rec._wb_kuormat_get_carrier()
            rec.wb_kuormat_show_price = bool(
                carrier and carrier.wb_kuormat_show_price_in_delivery
            )

    @api.depends('carrier_id.delivery_type')
    def _compute_wb_kuormat_is_kuormat(self):
        for rec in self:
            carrier = rec._wb_kuormat_get_carrier()
            rec.wb_kuormat_is_kuormat = bool(
                carrier and carrier.delivery_type == 'wb_kuormat'
            )

    def _wb_kuormat_is_dropship(self):
        """True when goods ship vendor → customer (dropship route)."""
        self.ensure_one()
        if 'is_dropship' in self._fields:
            return self.is_dropship
        return (
            self.location_id.usage == 'supplier'
            and self.location_dest_id.usage == 'customer'
        )

    def _wb_kuormat_get_sale_order(self):
        """Resolve the linked sale order (Odoo 19 stock.reference aware)."""
        self.ensure_one()
        if self.sale_id:
            return self.sale_id
        if 'reference_ids' in self._fields and self.reference_ids:
            sale_orders = self.reference_ids.sale_ids
            if sale_orders:
                return sale_orders[0]
        sale_orders = self.move_ids.sale_line_id.order_id
        if sale_orders:
            return sale_orders[0]
        if self.purchase_id:
            po_lines = self.purchase_id.order_line
            if 'sale_line_id' in po_lines._fields:
                sale_lines = po_lines.mapped('sale_line_id')
                if sale_lines:
                    return sale_lines[0].order_id
            if 'sale_order_id' in po_lines._fields:
                sale_orders = po_lines.mapped('sale_order_id')
                if sale_orders:
                    return sale_orders[0]
        return self.env['sale.order']

    def _wb_kuormat_get_carrier(self):
        """Find the relevant carrier, especially for dropship pickings."""
        self.ensure_one()
        if self.carrier_id:
            return self.carrier_id
        order = self._wb_kuormat_get_sale_order()
        return order.carrier_id if order else self.env['delivery.carrier']

    def _wb_kuormat_get_sender_partner(self, sale_order=None):
        """From address: vendor on dropship, warehouse/company otherwise."""
        self.ensure_one()
        order = sale_order or self._wb_kuormat_get_sale_order()
        if self._wb_kuormat_is_dropship():
            if self.purchase_id:
                return self.purchase_id.partner_id
            vendors = self.move_ids.purchase_line_id.order_id.partner_id
            if vendors:
                return vendors[0]
        if order and order.warehouse_id.partner_id:
            return order.warehouse_id.partner_id
        return self.company_id.partner_id

    def _wb_kuormat_get_receiver_partner(self, sale_order=None):
        """To address: customer shipping on dropship, picking partner otherwise."""
        self.ensure_one()
        order = sale_order or self._wb_kuormat_get_sale_order()
        if self._wb_kuormat_is_dropship() and order:
            return order.partner_shipping_id or order.partner_id
        return self.partner_id

    def _wb_kuormat_get_shipment_freetext(self, sale_order=None):
        """References shown on the carrier label for customer and warehouse."""
        self.ensure_one()
        order = sale_order or self._wb_kuormat_get_sale_order()
        note_content = html.fromstring(self.note).text_content() if self.note else self.name
        return {
            'invoiceReference': self.origin,
            'delivery': note_content,
            'addressCard': (order.client_order_ref or order.name) if order else '-',
        }

    def _wb_kuormat_propagate_carrier(self):
        """Copy SO carrier onto pickings that do not have one yet."""
        for picking in self.filtered(lambda p: not p.carrier_id):
            order = picking._wb_kuormat_get_sale_order()
            if order and order.carrier_id:
                picking.carrier_id = order.carrier_id

    @api.model_create_multi
    def create(self, vals_list):
        pickings = super().create(vals_list)
        pickings._wb_kuormat_propagate_carrier()
        return pickings

    def write(self, vals):
        res = super().write(vals)
        if {'sale_id', 'reference_ids', 'move_ids'} & set(vals):
            self._wb_kuormat_propagate_carrier()
        return res

    def action_open_kuormat_wizard(self):
        self.ensure_one()
        self._wb_kuormat_propagate_carrier()
        carrier = self._wb_kuormat_get_carrier()
        return {
            'name': 'Book Kuormat.Com Shipment',
            'type': 'ir.actions.act_window',
            'res_model': 'wb.kuormat.book.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
                'default_carrier_id': carrier.id if carrier else False,
            },
        }

    def action_get_kuormat_labels(self):
        self.ensure_one()
        self._wb_kuormat_propagate_carrier()
        carrier = self._wb_kuormat_get_carrier()
        if carrier and getattr(carrier, 'wb_kuormat_send_shipping', None):
            res = carrier.wb_kuormat_send_shipping(self)
            self.message_post(body=_("Labels generated for Kuormat.Com shipments"))
            return res
        return False
