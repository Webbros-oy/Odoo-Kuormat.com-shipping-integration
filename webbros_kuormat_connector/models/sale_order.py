from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    wb_kuormat_carrier = fields.Selection([
        ('postnord', 'PostNord'),
        ('dhl', 'DHL')
    ], string="Kuormat Sub-Carrier")

    def write(self, vals):
        res = super().write(vals)
        if 'carrier_id' in vals:
            self._wb_kuormat_propagate_carrier_to_pickings()
        return res

    def action_confirm(self):
        res = super().action_confirm()
        self._wb_kuormat_propagate_carrier_to_pickings()
        return res

    def _wb_kuormat_propagate_carrier_to_pickings(self):
        """Set carrier on related pickings (including dropship) from the SO."""
        Picking = self.env['stock.picking']
        for order in self.filtered('carrier_id'):
            pickings = order.picking_ids.filtered(lambda p: not p.carrier_id)
            if order.stock_reference_ids:
                ref_pickings = Picking.search([
                    ('reference_ids', 'in', order.stock_reference_ids.ids),
                    ('carrier_id', '=', False),
                ])
                pickings |= ref_pickings
            if pickings:
                pickings.write({'carrier_id': order.carrier_id.id})
