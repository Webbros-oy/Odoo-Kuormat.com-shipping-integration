from odoo import api, fields, models, _
from odoo.exceptions import UserError
import requests
import logging
from markupsafe import Markup

_logger = logging.getLogger(__name__)

class DeliveryCarrier(models.Model):
    """
    Extends delivery.carrier to integrate with the Kuormat Delivery API.
    Provides fields for API credentials, default shipment dimensions, and
    methods for rating, booking, and managing Kuormat shipments.
    """
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(
        selection_add=[('wb_kuormat', 'Delivery Kuormat.Com')],
        ondelete={'wb_kuormat': 'set default'}
    )

    wb_kuormat_api_key = fields.Char(string='API Key', groups='base.group_system')
    wb_kuormat_api_secret = fields.Char(string='Customer ID', groups='base.group_system')
    wb_kuormat_test_mode = fields.Boolean(string='Kuormat.Com Test Mode', default=False)
    wb_kuormat_partner_id = fields.Char(string='Partner ID', groups='base.group_system', default='Odoo-537194', help="Partner Reference ID given by Kuormat.Com")

    # Control fields
    wb_kuormat_show_price_in_delivery = fields.Boolean("Show Price in Delivery Document")
    wb_kuormat_update_sale_price = fields.Boolean("Update Sale Price from Shipment")

    # Sub-Carriers
    wb_kuormat_fetch_postnord = fields.Boolean("Fetch PostNord Price", default=True)
    wb_kuormat_fetch_dhl = fields.Boolean("Fetch DHL Price", default=True)

    # Defaults
    wb_kuormat_default_shipment_type_id = fields.Many2one('wb.kuormat.shipment.types', string="Shipment Type")
    wb_kuormat_default_length = fields.Integer("Default Length (cm)")
    wb_kuormat_default_width = fields.Integer("Default Width (cm)")
    wb_kuormat_default_height = fields.Integer("Default Height (cm)")
    wb_kuormat_stackable = fields.Boolean("Stackable")
    wb_kuormat_dangerous_goods = fields.Boolean("Contains dangerous goods")
    wb_kuormat_call_before_delivery = fields.Boolean("Call before delivery")
    wb_kuormat_attended = fields.Boolean("Attended")
    wb_kuormat_signature_assurance = fields.Boolean("Signature assurance")
    wb_kuormat_book_pickup = fields.Boolean("Book Pickup", default=True,
        help="If enabled, automatically books a PostNord pickup and generates labels on shipment creation.")

    @api.onchange('wb_kuormat_default_shipment_type_id')
    def _onchange_wb_kuormat_default_shipment_type_id(self):
        if self.wb_kuormat_default_shipment_type_id:
            self.wb_kuormat_default_length = self.wb_kuormat_default_shipment_type_id.default_length
            self.wb_kuormat_default_width = self.wb_kuormat_default_shipment_type_id.default_width
            self.wb_kuormat_default_height = self.wb_kuormat_default_shipment_type_id.default_height

    def _wb_kuormat_make_request(self, endpoint, payload, method='POST'):
        """
        Makes a standard HTTP request to the Kuormat API.

        Args:
            endpoint (str): The API endpoint path (e.g., 'price', 'shipment').
            payload (dict): The JSON payload to be sent.
            method (str): HTTP method to use (default 'POST').

        Returns:
            dict: The parsed JSON response from the API, or a dict containing an 'error'.
        """
        self.ensure_one()
        domain = 'test-api.kuormat.com' if self.wb_kuormat_test_mode else 'api.kuormat.com'
        url = f"https://{domain}/v1/{endpoint.lstrip('/')}"

        headers = {
            'Content-Type': 'application/json',
            'api-key': self.wb_kuormat_api_key,
            'customer-id': self.wb_kuormat_api_secret,
            'partner-id': self.wb_kuormat_partner_id or 'Odoo-537194',
        }

        try:
            if getattr(self, 'debug_logging', False):
                _logger.info("Kuormat API Request [%s]: %s\nPayload: %s", method, url, payload)

            # We use json=payload to ensure it's sent as application/json
            response = requests.request(method, url, json=payload, headers=headers, timeout=15)

            if getattr(self, 'debug_logging', False):
                _logger.info("Kuormat API Response [%s]:\n%s", response.status_code, response.text)

            if response.status_code != 200:
                _logger.error("Kuormat API Error Detail: %s", response.text)

            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError:
            # Return the JSON error body if available
            try:
                err_res = response.json()
                if getattr(self, 'debug_logging', False):
                    _logger.error("Kuormat API HTTPError Response: %s", err_res)
                return err_res
            except:
                return {'error': response.text}
        except Exception as e:
            return {'error': str(e)}

    def  wb_kuormat_rate_shipment(self, order):
        """
        Rates a shipment based on the provided sale order.
        Calculates price using the 'price' endpoint of the Kuormat API.

        Args:
            order (recordset): The sale.order requiring a shipping rate.

        Returns:
            dict: Containing 'success', 'price', 'error_message', and 'warning_message'.
        """
        self.ensure_one()

        # Validation requires specific countries
        allowed_countries = ['FI', 'EE', 'LV', 'LT', 'SE', 'DK', 'DE', 'FR', 'LU', 'NL', 'BE', 'AT', 'PL', 'CZ', 'HU', 'SK', 'SI', 'IE', 'IT', 'ES', 'PT', 'HR', 'BG', 'RO', 'GR']

        sender_country = self.company_id.country_id.code
        receiver_country = order.partner_shipping_id.country_id.code

        # Calculate total weight
        total_weight = self.env.context.get('order_weight') or sum(line.product_id.weight * line.product_uom_qty for line in order.order_line) or 1.0

        num_items = self.env.context.get('wb_kuormat_number_of_items') or 1
        num_items = int(num_items) if int(num_items) > 0 else 1
        weight_per_item = total_weight / num_items

        sender_zip = order.warehouse_id.partner_id.zip or self.company_id.zip or '00100'
        sender_cc = order.warehouse_id.partner_id.country_id.code or self.company_id.country_id.code

        recv_zip = order.partner_shipping_id.zip or '33100'
        recv_cc = order.partner_shipping_id.country_id.code

        carriers_to_fetch = []
        if self.wb_kuormat_fetch_postnord:
            carriers_to_fetch.append('postnord')
        if self.wb_kuormat_fetch_dhl:
            carriers_to_fetch.append('dhl')
        if not carriers_to_fetch:
            carriers_to_fetch = ['postnord']

        payload = {
            'shipments': [{
                'carriers': carriers_to_fetch,
                'sender': {
                    'postalCode': sender_zip,
                    'countryCode': sender_cc if sender_cc in allowed_countries else 'FI',
                },
                'receiver': {
                    'postalCode': recv_zip,
                    'countryCode': recv_cc if recv_cc in allowed_countries else 'FI',
                    'type': 'company' if order.partner_shipping_id.is_company else 'person',
                },
                'deliveryToPickupPoint': False,
                'pieces': [{
                    'type': self.wb_kuormat_default_shipment_type_id.name.lower() if self.wb_kuormat_default_shipment_type_id else 'parcel',
                    'amount': 1,
                    'weight': int(max(1, round(weight_per_item))),
                    'length': self.wb_kuormat_default_length or 10,
                    'width': self.wb_kuormat_default_width or 10,
                    'height': self.wb_kuormat_default_height or 10,
                    'stackable': self.wb_kuormat_stackable,
                    'description': order.name or 'Goods',
                }]
            }]
        }

        res = self._wb_kuormat_make_request('price', payload)

        # Check root level error
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
            raise UserError(_("Kuormat Pricing Error: %s") % err_msg)
        if 'errors' in res:
            errors = res['errors']
            err_msg = ", ".join([str(e) for e in errors]) if isinstance(errors, list) else str(errors)
            raise UserError(_("Kuormat Pricing Error: %s") % err_msg)

        # Extract price from the response shipments array
        try:
            shipment_res = res.get('shipments', [{}])[0]

            # Check shipment level error
            if 'error' in shipment_res:
                err_data = shipment_res['error']
                if isinstance(err_data, dict):
                    err_msg = err_data.get('message') or str(err_data)
                    body_errors = err_data.get('body')
                    if isinstance(body_errors, list):
                        details = "\n".join([f"• {b.get('path', 'Field')}: {b.get('message', '')}" for b in body_errors if isinstance(b, dict)])
                        if details:
                            err_msg += "\n\nDetails:\n" + details
                else:
                    err_msg = str(err_data)
                raise UserError(_("Kuormat Pricing Error: %s") % err_msg)

            if 'errors' in shipment_res:
                errors = shipment_res['errors']
                if isinstance(errors, list):
                    err_msgs = []
                    for e in errors:
                        if isinstance(e, dict):
                            err_msgs.append(e.get('message') or str(e))
                        else:
                            err_msgs.append(str(e))
                    raise UserError(_("Kuormat Pricing Error:\n%s") % "\n".join(err_msgs))
                else:
                    raise UserError(_("Kuormat Pricing Error: %s") % str(errors))

            if 'prices' in shipment_res and shipment_res['prices']:
                # Find minimum price
                best_price_obj = min(
                    [p for p in shipment_res['prices'] if p.get('price') is not None],
                    key=lambda x: x.get('price', float('inf')),
                    default={}
                )
                price = best_price_obj.get('price', 0.0)
                best_carrier = best_price_obj.get('priceType') or best_price_obj.get('carrier') or 'postnord'
            else:
                price = shipment_res.get('totalPrice', 0.0)
                best_carrier = shipment_res.get('priceType') or 'postnord'

            if best_carrier:
                order.wb_kuormat_carrier = best_carrier.lower()

        except UserError:
            raise
        except (IndexError, KeyError, TypeError, ValueError) as e:
            raise UserError(f"Kuormat API parsing error: {e}\nResponse: {res}")

        return {
            'success': True,
            'price': float(price),
            'wb_kuormat_carrier': best_carrier,
            'error_message': False,
            'warning_message': False
        }

    def rate_shipment(self, order):
        res = super(DeliveryCarrier, self).rate_shipment(order)
        if self.delivery_type == 'wb_kuormat' and res.get('success'):
            num_items = self.env.context.get('wb_kuormat_number_of_items')
            if num_items:
                num_items = int(num_items)
                if num_items > 1:
                    res['price'] = res['price'] * num_items
                    if 'carrier_price' in res:
                        res['carrier_price'] = res['carrier_price'] * num_items
        return res

    def wb_kuormat_send_shipping(self, pickings):
        """
        Fetches labels for all Kuormat shipments linked to the given pickings
        and attaches the resulting PDF(s) to the picking document.

        Args:
            pickings (recordset): The stock.picking records to get labels for.

        Returns:
            list: A list of dicts returning success boolean and picking_id.
        """
        import base64
        res = []
        for picking in pickings:
            kuormat_shipments = picking.wb_kuormat_shipment_ids
            if not kuormat_shipments:
                raise UserError(_("No Kuormat shipments found for this transfer. Please book a shipment first."))

            # Collect all shipment IDs
            shipment_ids = [s.shipment_id for s in kuormat_shipments if s.shipment_id]
            if not shipment_ids:
                raise UserError(_("Kuormat shipments have no valid Shipment IDs. Cannot fetch labels."))

            # Build query string: GET /v1/labels?ids=ID1,ID2
            ids_param = ','.join(shipment_ids)
            api_res = self._wb_kuormat_make_request(f'labels?ids={ids_param}', {}, method='GET')

            if 'error' in api_res:
                raise UserError(_("Kuormat Labels Error: %s") % api_res['error'])

            # API may return PDF directly as base64 or a URL
            label_b64 = api_res.get('labelBase64') or api_res.get('label_base64', '')
            label_url = api_res.get('labelUrl') or api_res.get('label_url', '')

            if not label_b64 and not label_url:
                labels_data = api_res.get('labels')
                if isinstance(labels_data, list) and labels_data:
                    first_label = labels_data[0]
                    if isinstance(first_label, dict):
                        label_b64 = first_label.get('labelBase64') or first_label.get('base64', '') or first_label.get('pdf', '')
                        label_url = first_label.get('labelUrl') or first_label.get('url', '')
                elif isinstance(labels_data, dict):
                    label_b64 = labels_data.get('labelBase64') or labels_data.get('base64', '') or labels_data.get('pdf', '')
                    label_url = labels_data.get('labelUrl') or labels_data.get('url', '')
                elif isinstance(labels_data, str):
                    if labels_data.startswith('http'):
                        label_url = labels_data
                    else:
                        label_b64 = labels_data

            if label_b64:
                attachment = self.env['ir.attachment'].create({
                    'name': f'Kuormat-Labels-{picking.name}.pdf',
                    'type': 'binary',
                    'datas': label_b64,
                    'res_model': 'stock.picking',
                    'res_id': picking.id,
                    'mimetype': 'application/pdf',
                })
                picking.message_post(
                    body=_("Kuormat labels attached."),
                    attachment_ids=[attachment.id]
                )
            elif label_url:
                picking.message_post(body=Markup("{} <a href='{}' target='_blank'>{}</a>").format(_("Kuormat label available at:"), label_url, label_url))
            else:
                _logger.warning("Kuormat labels response did not contain a recognizable label field: %s", api_res)
                picking.message_post(body=_("Kuormat: Labels fetched but could not extract PDF. Please check API response."))

            res.append({'success': True, 'picking_id': picking.id})
        return res

    def wb_kuormat_get_tracking_link(self, picking):
        """
        Returns the tracking URL for the given picking.

        Args:
            picking (recordset): The stock.picking containing the tracking reference.

        Returns:
            str: The tracking URL as a string.
        """
        self.ensure_one()
        # Attempt to find the first associated Kuormat package URL
        if picking.wb_kuormat_shipment_ids:
            first_shipment = picking.wb_kuormat_shipment_ids[0]
            if first_shipment.package_ids:
                first_package = first_shipment.package_ids[0]
                if first_package.url:
                    return first_package.url

        # Fallback to standard URL layout if no nested package URLs exist
        return f'https://kuormat.com/track/{picking.carrier_tracking_ref}'

    def wb_kuormat_cancel_shipment(self, pickings):
        """
        Cancels the shipment.

        Args:
            pickings (recordset): The stock.picking records to cancel.
        """
        for picking in pickings:
            if not picking.carrier_tracking_ref:
                continue

            payload = {'tracking_number': picking.carrier_tracking_ref}
            api_res = self._wb_kuormat_make_request(
                f'shipment/{picking.carrier_tracking_ref}',
                payload,
                method='DELETE'
            )

            if 'error' in api_res:
                raise UserError(_("Failed to cancel Kuormat shipment: %s") % api_res['error'])

            picking.message_post(body=_("Shipment %s cancelled with Kuormat") % picking.carrier_tracking_ref)
