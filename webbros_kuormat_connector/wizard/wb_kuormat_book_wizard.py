from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
from markupsafe import Markup

_logger = logging.getLogger(__name__)

class WbKuormatBookWizard(models.TransientModel):
    """
    Wizard for booking a Kuormat.com shipment from a stock picking.
    Allows adjusting default shipment parameters (weights, dimensions)
    and fetching estimated prices before confirming the booking.
    """
    _name = 'wb.kuormat.book.wizard'
    _description = 'Book Kuormat.com Shipment Wizard'

    picking_id = fields.Many2one('stock.picking', string='Transfer', required=True)
    carrier_id = fields.Many2one('delivery.carrier', string='Carrier', required=True)
    price = fields.Float('Estimated Price', readonly=True)
    wb_kuormat_carrier = fields.Selection([
        ('postnord', 'PostNord'),
        ('dhl', 'DHL')
    ], string='Transport Carrier', required=True, default='postnord')
    line_ids = fields.One2many('wb.kuormat.book.wizard.line', 'wizard_id', string='Shipment Lines')
    currency_id = fields.Many2one(related='picking_id.company_id.currency_id')

    @api.model
    def default_get(self, fields_list):
        """
        Populates default wizard data based on the selected picking and carrier defaults.
        """
        res = super(WbKuormatBookWizard, self).default_get(fields_list)
        if res.get('picking_id') and res.get('carrier_id'):
            picking = self.env['stock.picking'].browse(res['picking_id'])
            carrier = self.env['delivery.carrier'].browse(res['carrier_id'])

            # Simple mode: 1 line prefilled from carrier defaults
            shipment_type = carrier.wb_kuormat_default_shipment_type_id

            order = picking._wb_kuormat_get_sale_order()
            if order and order.wb_kuormat_carrier:
                res['wb_kuormat_carrier'] = order.wb_kuormat_carrier
            elif getattr(carrier, 'wb_kuormat_fetch_postnord', False) and not getattr(carrier, 'wb_kuormat_fetch_dhl', False):
                res['wb_kuormat_carrier'] = 'postnord'
            elif getattr(carrier, 'wb_kuormat_fetch_dhl', False) and not getattr(carrier, 'wb_kuormat_fetch_postnord', False):
                res['wb_kuormat_carrier'] = 'dhl'

            lines = [(0, 0, {
                'wb_kuormat_shipment_type_id': shipment_type.id if shipment_type else False,
                'weight': picking.shipping_weight or 1.0,
                'length': carrier.wb_kuormat_default_length or 10,
                'width': carrier.wb_kuormat_default_width or 10,
                'height': carrier.wb_kuormat_default_height or 10,
                'stackable': carrier.wb_kuormat_stackable,
                'amount': 1,
            })]
            res['line_ids'] = lines
        return res

    # Full list of countries supported by Kuormat API
    KUORMAT_ALLOWED_COUNTRIES = [
        'FI', 'EE', 'LV', 'LT', 'SE', 'DK', 'NO', 'DE', 'FR', 'LU', 'NL', 'BE',
        'AT', 'PL', 'CZ', 'HU', 'SK', 'SI', 'IE', 'IT', 'ES', 'PT', 'HR', 'BG',
        'RO', 'GR', 'CH', 'LI', 'GB', 'MT', 'CY',
    ]

    def action_get_price(self):
        """
        Builds the validation payload and requests an estimated price from the Kuormat.com API.
        Reloads the wizard with the calculated price for user confirmation.
        """
        self.ensure_one()
        allowed_countries = self.KUORMAT_ALLOWED_COUNTRIES
        picking = self.picking_id
        picking._wb_kuormat_propagate_carrier()
        order = picking._wb_kuormat_get_sale_order()
        if not order:
            raise UserError(_("No Sale Order linked to this transfer. Cannot fetch price."))

        sender_partner = picking._wb_kuormat_get_sender_partner(order)
        receiver_partner = picking._wb_kuormat_get_receiver_partner(order)

        sender_zip = sender_partner.zip or self.env.company.zip or '00100'
        sender_cc = sender_partner.country_id.code or self.env.company.country_id.code

        if sender_cc not in allowed_countries:
            sender_cc = 'FI'
            sender_zip = '00100'

        recv_zip = receiver_partner.zip or '33100'
        recv_cc = receiver_partner.country_id.code

        if recv_cc not in allowed_countries:
            recv_cc = 'FI'
            recv_zip = '33100'

        pieces = []
        for line in self.line_ids:
            for i in range(line.amount):
                pieces.append({
                    'type': line.wb_kuormat_shipment_type_id.name.lower() if line.wb_kuormat_shipment_type_id else 'parcel',
                    'amount': 1,
                    'weight': int(max(1, round(line.weight))),
                    'length': line.length,
                    'width': line.width,
                    'height': line.height,
                    'stackable': line.stackable,
                    'description': picking.name or 'Goods',
                })

        payload = {
            'shipments': [{
                'carriers': [self.wb_kuormat_carrier],
                'sender': {
                    'postalCode': sender_zip,
                    'countryCode': sender_cc if sender_cc in allowed_countries else 'FI',
                },
                'receiver': {
                    'postalCode': recv_zip,
                    'countryCode': recv_cc if recv_cc in allowed_countries else 'FI',
                    'type': 'company' if receiver_partner.is_company else 'person',
                },
                'deliveryToPickupPoint': False,
                'pieces': pieces
            }]
        }

        res = self.carrier_id._wb_kuormat_make_request('price', payload)
        if 'error' in res:
            err_data = res['error']
            if isinstance(err_data, dict):
                err_msg = err_data.get('message') or str(err_data)
                body_errors = err_data.get('body')
                if isinstance(body_errors, list):
                    details = "\n".join([f"• {b.get('path', 'Field')}: {b.get('message', '')}" for b in body_errors if isinstance(b, dict)])
                    if details:
                        err_msg += "\n\nDetails:\n" + details
            else:
                err_msg = str(err_data)
            raise UserError(_("Kuormat.com API Error: %s") % err_msg)

        try:
            shipment_res = res.get('shipments', [{}])[0]
            if 'prices' in shipment_res and shipment_res['prices']:
                prices_list = [p.get('price', 0.0) for p in shipment_res['prices'] if p.get('price') is not None]
                price = min(prices_list) if prices_list else 0.0
            else:
                price = shipment_res.get('totalPrice', 0.0)
        except (IndexError, KeyError, TypeError, ValueError):
            price = 0.0

        if price > 0.0:
            total_pieces = sum(line.amount for line in self.line_ids) or 1
            price = price * (1.0 + (self.carrier_id.margin / 100.0)) + (self.carrier_id.fixed_margin * total_pieces)

        self.price = price

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wb.kuormat.book.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_book_shipment(self):
        """
        Validates sender/receiver requirements and generates actual Kuormat.com shipments.
        Writes the returned tracking codes and pricing data back to Odoo models.
        """
        self.ensure_one()
        allowed_countries = self.KUORMAT_ALLOWED_COUNTRIES
        picking = self.picking_id
        picking._wb_kuormat_propagate_carrier()
        order = picking._wb_kuormat_get_sale_order()

        company = self.env.company
        sender_partner = picking._wb_kuormat_get_sender_partner(order)
        receiver = picking._wb_kuormat_get_receiver_partner(order)

        # --- Sender Validation ---
        errors = []
        sender_zip = sender_partner.zip or company.zip
        sender_cc = sender_partner.country_id.code or company.country_id.code
        sender_city = sender_partner.city or company.city
        sender_street = sender_partner.street or company.street
        sender_name = sender_partner.name or company.name
        sender_phone = sender_partner.phone or company.phone
        sender_email = sender_partner.email or company.email

        if not sender_name:
            errors.append(_("Sender: Company name is missing. Please configure it in Settings > Companies."))
        if not sender_street:
            errors.append(_("Sender: Street address is missing. Please update the warehouse or company address."))
        if not sender_zip:
            errors.append(_("Sender: Postal code is missing. Please update the warehouse or company address."))
        if not sender_city:
            errors.append(_("Sender: City is missing. Please update the warehouse or company address."))
        if not sender_cc:
            errors.append(_("Sender: Country is not set. Please update the warehouse or company address."))
        elif sender_cc not in allowed_countries:
            errors.append(_("Sender country '%s' is not supported by Kuormat.Com. Please set a supported European country on your company or warehouse address.") % sender_cc)
        if not sender_phone and not sender_email:
            errors.append(_("Sender: Either a phone number or email address is required. Please update the company settings."))

        # --- Receiver Validation ---
        recv_zip = receiver.zip
        recv_cc = receiver.country_id.code
        recv_city = receiver.city
        recv_street = receiver.street
        recv_name = receiver.name
        recv_phone = receiver.phone
        recv_email = receiver.email

        if not recv_name:
            errors.append(_("Receiver: Name is missing on the delivery address."))
        if not recv_street:
            errors.append(_("Receiver: Street address is missing on the delivery address."))
        if not recv_zip:
            errors.append(_("Receiver: Postal code is missing on the delivery address."))
        if not recv_city:
            errors.append(_("Receiver: City is missing on the delivery address."))
        if not recv_cc:
            errors.append(_("Receiver: Country is not set on the delivery address."))
        elif recv_cc not in allowed_countries:
            errors.append(_("Receiver country '%s' is not supported by Kuormat.Com. Supported countries: %s") % (recv_cc, ', '.join(allowed_countries)))
        if not recv_phone:
            errors.append(_("Receiver: Phone number is missing on the delivery address."))
        if not recv_email:
            errors.append(_("Receiver: Email is missing on the delivery address."))

        if errors:
            raise UserError(_("Cannot book Kuormat.Com shipment. Please fix the following:\n\n• %s") % "\n• ".join(errors))

        pieces = []
        earliest_date_str = picking.scheduled_date.strftime('%Y-%m-%d') if picking.scheduled_date else None
        for line in self.line_ids:
            for i in range(line.amount):
                pieces.append({
                    'type': line.wb_kuormat_shipment_type_id.name.lower() if line.wb_kuormat_shipment_type_id else 'parcel',
                    'amount': 1,
                    'weight': int(max(1, round(line.weight))),
                    'length': line.length,
                    'width': line.width,
                    'height': line.height,
                    'stackable': line.stackable,
                    'description': picking.name or 'Goods',
                })

        payload = {
            'bookPostnordPickup': self.carrier_id.wb_kuormat_book_pickup if self.wb_kuormat_carrier == 'postnord' else False,
            'shipments': [{
                'priceType': self.wb_kuormat_carrier,
                'freeText': picking._wb_kuormat_get_shipment_freetext(order),
                'sender': {
                    'company': sender_name,
                    'address': {
                        'street': sender_street,
                        'postalCode': sender_zip,
                        'city': sender_city,
                        'countryCode': sender_cc,
                    },
                    'phone': sender_phone,
                    'email': sender_email,
                },
                'receiver': {
                    'name': recv_name,
                    'type': 'company' if receiver.is_company else 'person',
                    'address': {
                        'street': recv_street,
                        'postalCode': recv_zip,
                        'city': recv_city,
                        'countryCode': recv_cc,
                    },
                    'phone': recv_phone,
                    'email': recv_email or '',
                },
                'earliestPickupDate' : earliest_date_str,
                'deliveryToPickupPoint': False,
                'pieces': pieces
            }]
        }

        api_res = self.carrier_id._wb_kuormat_make_request('shipment', payload)

        if isinstance(api_res, dict) and 'error' in api_res:
            err_data = api_res['error']
            if isinstance(err_data, dict):
                err_msg = err_data.get('message') or str(err_data)
                body_errors = err_data.get('body')
                if isinstance(body_errors, list):
                    details = "\n".join([f"• {b.get('path', 'Field')}: {b.get('message', '')}" for b in body_errors if isinstance(b, dict)])
                    if details:
                        err_msg += "\n\nDetails:\n" + details
            else:
                err_msg = str(err_data)
            raise UserError(_("Kuormat.Com Booking Error: %s") % err_msg)
        if isinstance(api_res, dict) and api_res.get('code'):
            raise UserError(_("Kuormat.Com API Error [%s]: %s") % (api_res.get('code'), api_res.get('message', '')))

        shipments_created = api_res.get('shipments', []) if isinstance(api_res, dict) else []
        first_tracking = False
        total_price = 0.0
        new_shipment_recs = self.env['wb.kuormat.shipment']

        for ship in shipments_created:
            tracking_number = ship.get('trackingCode') or ship.get('trackingNumber')

            if not tracking_number:
                labels_data = ship.get('labels', [])
                if isinstance(labels_data, list) and labels_data:
                    tracking_number = labels_data[0].get('trackingCode') or labels_data[0].get('trackingNumber')
                elif isinstance(labels_data, dict):
                    tracking_number = labels_data.get('trackingCode') or labels_data.get('trackingNumber')

            if not tracking_number:
                pieces_data = ship.get('pieces', [])
                if isinstance(pieces_data, list) and pieces_data:
                    tracking_number = pieces_data[0].get('trackingCode') or pieces_data[0].get('trackingNumber')

            if not tracking_number:
                tracking_number = ship.get('id') or 'UNKNOWN'

            if not first_tracking:
                first_tracking = tracking_number

            ship_price = 0.0
            if 'prices' in ship and ship['prices']:
                prices_list = [p.get('price', 0.0) for p in ship['prices'] if p.get('price') is not None]
                ship_price = min(prices_list) if prices_list else 0.0
            elif ship.get('price'):
                ship_price = float(ship.get('price', 0.0))
            elif ship.get('totalPrice'):
                ship_price = float(ship.get('totalPrice', 0.0))

            total_price += ship_price
            carrier_data = ship.get('carrierData') or {}
            carrier_name = carrier_data.get('name') or False
            pickup_id = ship.get('pickupId') or carrier_data.get('pickupId') or carrier_data.get('transportId')
            earliest_date = ship.get('earliestPickupDate') or ship.get('earliestDate') or carrier_data.get('earliestPickupDate') or carrier_data.get('earliestDate')

            # --- Extract package tracking URLs ---
            carrier_tracking_url = carrier_data.get('transportTrackingUrl') or carrier_data.get('trackingUrl') or carrier_data.get('tracking_url') or carrier_data.get('tracking-URL') or carrier_data.get('tracking-url')
            package_lines = []
            items_data = ship.get('items', []) or carrier_data.get('items', [])
            if isinstance(items_data, list):
                for item in items_data:
                    if isinstance(item, dict):
                        p_id = item.get('id')
                        p_url = item.get('trackingUrl') or item.get('tracking_url') or carrier_tracking_url
                        if p_id or p_url:
                            package_lines.append((0, 0, {
                                'pack_id': p_id,
                                'url': p_url
                            }))

            if not package_lines and carrier_tracking_url:
                package_lines.append((0, 0, {
                    'pack_id': tracking_number,
                    'url': carrier_tracking_url
                }))

            new_shipment_recs |= self.env['wb.kuormat.shipment'].create({
                'picking_id': self.picking_id.id,
                'carrier_id': self.carrier_id.id,
                'carrier_name': carrier_name,
                'pickup_id': pickup_id,
                'shipment_id': tracking_number,
                'price': ship_price,
                'earliest_date': earliest_date,
                'package_ids': package_lines,
            })

        # --- Set Odoo standard fields ---
        if first_tracking:
            write_vals = {'carrier_tracking_ref': first_tracking}
            if not self.picking_id.carrier_id:
                write_vals['carrier_id'] = self.carrier_id.id
            self.picking_id.write(write_vals)

        # --- Update Sale Price if configured ---
        if self.carrier_id.wb_kuormat_update_sale_price and order and total_price > 0:
            total_pieces = sum(line.amount for line in self.line_ids) or 1
            price_with_margin = total_price * (1.0 + (self.carrier_id.margin / 100.0)) + (self.carrier_id.fixed_margin * total_pieces)
            delivery_lines = order.order_line.filtered(lambda l: l.is_delivery)
            if delivery_lines:
                delivery_lines[0].price_unit = price_with_margin
            else:
                _logger.warning("wb_kuormat: No delivery line found on SO %s to update price.", order.name)

        msg_parts = [Markup("<b>{}</b><br/>").format(_("Kuormat.Com shipments booked successfully."))]
        for ship_rec in new_shipment_recs:
            msg_parts.append(Markup("<b>{}:</b> {}").format(_("Shipment ID"), ship_rec.shipment_id or 'N/A'))
            if ship_rec.pickup_id:
                msg_parts.append(Markup("<b>{}:</b> {}").format(_("Pickup ID"), ship_rec.pickup_id))
            if ship_rec.earliest_date:
                msg_parts.append(Markup("<b>{}:</b> {}").format(_("Earliest Date"), ship_rec.earliest_date))

            if ship_rec.package_ids:
                urls = []
                for pkg in ship_rec.package_ids:
                    if pkg.url:
                        urls.append(Markup("<a href='{}' target='_blank'>{}</a>").format(pkg.url, pkg.pack_id or _('Track')))
                if urls:
                    msg_parts.append(Markup("<b>{}:</b> {}").format(_("Tracking URL"), Markup(", ").join(urls)))
            msg_parts.append(Markup("<br/>"))

        self.picking_id.message_post(body=Markup("<br/>").join(msg_parts))


class WbKuormatBookWizardLine(models.TransientModel):
    """
    Represents an individual package/piece within the Kuormat.com booking wizard.
    Used to define dimensions and weights of individual boxes before shipping.
    """
    _name = 'wb.kuormat.book.wizard.line'
    _description = 'Book Kuormat.com Shipment Wizard Line'

    wizard_id = fields.Many2one('wb.kuormat.book.wizard', required=True, ondelete='cascade')
    wb_kuormat_shipment_type_id = fields.Many2one('wb.kuormat.shipment.types', string='Type')
    weight = fields.Float(string='Weight (kg)', default=1.0)
    length = fields.Integer(string='Length (cm)')
    width = fields.Integer(string='Width (cm)')
    height = fields.Integer(string='Height (cm)')
    stackable = fields.Boolean(string='Stackable')
    amount = fields.Integer(string='Amount', default=1)
