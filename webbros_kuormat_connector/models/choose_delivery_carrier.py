# -*- coding: utf-8 -*-
from odoo import models, fields

class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = 'choose.delivery.carrier'

    wb_kuormat_number_of_items = fields.Integer(string="#-of-items", default=1)

    def update_price(self):
        self = self.with_context(wb_kuormat_number_of_items=self.wb_kuormat_number_of_items)
        return super(ChooseDeliveryCarrier, self).update_price()

    def button_confirm(self):
        self = self.with_context(wb_kuormat_number_of_items=self.wb_kuormat_number_of_items)
        return super(ChooseDeliveryCarrier, self).button_confirm()
