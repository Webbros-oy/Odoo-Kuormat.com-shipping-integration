=======================================
Werbbros Kuormat.com Shipment connector
=======================================

.. image:: ../static/description/icon.png
  :scale: 20%

.. contents:: Table of contents
   :local:


Overview
========

**Delivery Kuormat** is an Odoo delivery carrier integration that connects Odoo's
inventory and sales workflows to the `Kuormat <https://kuormat.com>`_ shipping platform.

.. image:: ../static/description/kuormat_com_logo.png
   :target: https://www.kuormat.com

Kuormat.com is a Finnish logistics-focused company that simplifies the ordering
of shipments and offers transport services in Finland, the Nordic countries,
he Baltics, and across Europe. Deliveries are handled either by Postnord or
a local carrier. The service includes shipment booking, address label generation,
and shipment tracking.



Features
========

- **Carrier configuration** — Adds a *Delivery Kuormat* carrier type to Odoo's standard
  delivery module. Configure API credentials, default package dimensions, and shipment
  options directly on the carrier record.

- **Shipment pricing** — Fetches real-time delivery prices from the Kuormat API based on
  sender/receiver postal codes, package type, weight, and dimensions.

- **Shipment booking wizard** — A step-by-step wizard on stock transfers allows operators
  to define individual package lines (type, weight, dimensions, quantity), preview the
  estimated price, and confirm the booking with a single click.

- **Automatic PostNord pickup booking** — When enabled, the module books a PostNord
  pickup at the same time as the shipment, reducing manual handling.

- **Label retrieval** — Fetches shipping labels from the Kuormat API and attaches them as
  PDF files directly to the transfer record.

- **Tracking links** — Provides a direct tracking URL per shipment so customers and
  operators can follow delivery progress on the `Kuormat tracking portal <https://kuormat.com>`_.

- **Shipment cancellation** — Supports cancelling booked shipments via the Kuormat API.

- **Sale price update** — Optionally updates the delivery line on the originating sale
  order with the actual carrier price returned by the API.

- **Test mode** — Switch between the live API (``api.kuormat.com``) and the test
  environment (``test-api.kuormat.com``) without changing credentials.

- **European coverage** — Supports shipments between Finland, the Baltic states,
  Scandinavia, and a wide range of other European countries as defined by the Kuormat API.

Supported package types
=======================

Pre-configured shipment types with default dimensions are included out of the box
(e.g. parcel, half pallet, full pallet). These can be extended or modified from the
Kuormat Shipment Types menu.

Configuration
=============

1. Go to **Inventory → Configuration → Delivery Methods** and create or edit a carrier.
2. Set the *Provider* to **Delivery Kuormat.com**.
3. Enter your **API Key**, **Customer ID**
4. Set default package dimensions and shipment type for automatic price calculations.
5. Enable *Test Mode* during setup to validate the integration without creating live
   shipments. Note that one needs access to particular test system in order to test.
   Also notice that enabling test mode requires user to be in debug mode.


Usage
=====

1. Confirm a sale order and validate the delivery transfer as usual.
2. On the transfer form, click **Book Kuormat Shipment** to open the booking wizard.
3. Adjust package lines if needed, click **Get Price** to preview the cost, then
   **Book Shipment** to confirm.
4. Use **Get Labels** to download and attach the shipping label PDF to the transfer.
5. The tracking reference and a direct tracking link are stored on the transfer record.

Dependencies
============

- ``delivery`` (Odoo Delivery Costs)
- ``stock`` (Odoo Inventory)


Known Issues / Roadmap
======================
* Supporting inbound deliveries is not yet available in public version, can be requested from Webbros directly
* Using several package types already in the sales phase is not yet supported
* Using Odoo package features is not yet supported, will be added in future releases
* Currently shipment cancelation only happens when the delivery is cancelled. There is no
 explicit cancelation directly available, other than logging into Kuormat.com portal to do that 


Author & Support
================

This module is developed by `Webbros <https://webbros.fi>`_ — a Finnish Odoo partner
offering development, integration, and support services.

- **Website:** https://www.webbros.fi/r/Eyq
- **Integrated service:** `Kuormat <https://kuormat.com>`_

.. image:: ../static/description/webbros_logo.png
  :scale: 50%
  :target: https://www.webbros.fi/r/Eyq

Webbros oy is Odoo official partner helping customers implement
and maintain their ERP operations in efficient way. We can provide Odoo
as turn-key solution, or simply help on the hard parts, depending on case.
Our services include business process re-design (BPR), configuration
of the product, technical implementations, building integrations,
helping with reporting, training and providing support and problem solving.


License
=======

LGPL-3
