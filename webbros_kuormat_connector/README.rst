=======================================
Werbbros Kuormat.com Shipment connector
=======================================

.. image:: static/description/icon.png
  :scale: 20%

.. contents::
   :local:

-----------------------
🇫🇮 Suomeksi
-----------------------

Yleiskuvaus
===========

**Webbros Kuormat.com connector** yhdistää Odoon kuormat.com kuljetustensuunnitteluun.

.. image:: static/description/kuormat_com_logo.png
   :target: https://www.kuormat.com

Kuormat.com on suomalainen logistiikkaan keskittynyt yritys, joka tarjoaa kuljetuspalveluita
Suomessa, pohjoismaissa, Baltiassa ja Euroopassa. Kuljetukset hoitaa joko Postnord, DHL,
tai paikallinen kuljetusliike. Palveluun kuuluu kuljetushintojen tiedustelu,  kuljetusten
varaus, osoitetarrojen tuottaminen ja lähetysten seuranta.


Kuormat.com integraation ominaisuudet
=====================================

- **Kuljetusliikkeen konfigurointi** — Lisää *Delivery Kuormat.com* -kuljetustyypin Odoon
  toimitustapoihin. Kuljetustyypin taakse voi ylläpitää API-tunnukset, oletuspakkauskoot
  ja lähetysasetukset siten, että tämä toimitustapa integroituu Kuormat.com järjestelmään

- **Lähetyshinnoittelu** — Hakee reaaliaikaiset toimitushinnat Kuormat.com -palvelusta
  lähettäjän ja vastaanottajan postinumeroiden, pakkauslajin, painon ja mittojen perusteella.
  Tähän kuljetuksen ostohintaan voi lisätä halutun katteen Odoon kuljetushinnoittelun vakio-
  ominaisuutena

- **Lähetysten varaus-avustin (wizard)** — Vaiheistettu avustin, jossa pakkauksen yhteydessä
  kerrotaan käytetyt kollit, joille tarvitaan kuljetus. Kullekin kollille voidaan määritellä
  tarkat tiedot (tyyppi, paino, mitat, määrä) perustuen ennalta annettuihin oletuksiin ja
  tuotteilla oleviin painotietoihin ja asiakkaan toimitusosoitteeseen. Kuljetuksille voidaan
  kysyä uusi hinta päivitetyillä kollitiedoilla ja päivittää se tilauksen kuljetusriville,
  jos niin halutaan. Kuljetuksen voi myös varata yhdellä klikkauksella.

- **Automaattinen nouto** — Jos näin on valittu, varataan nouto
  lähetykselle automaattisesti halutulle päivälle. Tyypillisesti kuljetusliike hakee
  kollit kootusti päivittäin tai tiettyinä viikonpäivinä volyymien ja sopimuksen mukaan.

- **Osoitetarrojen haku** — Hakee osoitetarrat Kuormat-rajapinnasta ja liittää ne
  PDF-tiedostoina suoraan kuljetusdokumenttiin chatterin kautta. Siitä ne on tulostettavissa
  tarroiksi siten, että tarrapohja on suoraan kuljetusliikkeen mukainen ja nopeasti
  skannattavissa noudon yhteydessä

- **Seurantalinkit** — Tarjoaa suoran seurantalinkin jokaiselle lähetykselle, jotta
  asiakkaat ja muut asianosaiset voivat seurata toimituksen etenemistä reaaliajassa
  `Kuormat-seurantaportaalissa <https://kuormat.com>`_.

- **Lähetyksen peruutus** — Tukee varattujen lähetysten peruuttamista Kuormat-rajapinnan kautta.

- **Myyntihinnan päivitys** — Päivittää valinnaisesti alkuperäisen myyntitilauksen
  toimitusrivin todellisella lopullisella hinnalla, kun tarvittujen pakkausten määrä ja
  painot ovat lopullisesti selvillä. Tämä toiminto on käytettävissä mutta ei pakollinen

- **Euroopan kattavuus** — Tukee lähetyksiä Suomen, Baltian maiden, Skandinavian ja
  laajan eurooppalaisten maiden joukon välillä Kuormat-rajapinnan määrittelemällä tavalla.

Tuetut pakkaustyypit
====================

Valmiiksi määritellyt pakkaustyypit oletusmittoineen tulevat moduuliin alkuasetuksina
vastaten Kuormat.com palvelun tuettuja kollityyppejä (esim. paketti, puolilava, täysilava).
Kollityyppejä voi lisätä tarpeen mukaan jos niitä tulee palveluun lisää.

Yhdestä pakkaustyypistä (kuten vaikka paketti) voi Odoon sisällä tehdä tarpeen mukaan useita
toimitustapoja, tyypillisesti siten että mitat on jo valmiiksi ylläpidetty pakkaustyypille.
Näin voi Odoossa yhdellä koodilla valita ja välittää palveluun paketin mitat .


Konfigurointi
=============

1. Mene kohtaan **Varasto → Asetukset → Toimitustavat** ja luo tai muokkaa kuljetusliikettä.
2. Aseta *Toimittaja*-kentäksi **Delivery Kuormat**.
3. Syötä **Asiakastunnus** ja **API-avain**, jotka saat Kuormat.com profiiliasetuksista .
4. Aseta oletuspakkausmitat ja lähetystyyppi automaattista hintalaskentaa varten.


Käyttö
======

1. Vahvista myyntitilaus ja validoi toimitus normaalisti.
2. Toimituksella klikkaa **Varaa Kuormat-lähetys** avataksesi varausavustimen.
3. Säädä pakkausrivejä vastaamaan todellista paketointia, klikkaa **Hae hinta** päivittääksesi kustannukset,
   sitten **Varaa lähetys** vahvistaaksesi.
4. Käytä **Hae tarrat** -painiketta ladataksesi ja liittääksesi osoitetarrat PDF-muodossa toimitusdokumenttiin.
5. Seurantaviite ja suora seurantalinkki tallennetaan dokumentille ja ovat hyödynnettävissä toimitusviestillä.

Riippuvuudet
============

- ``delivery`` (Odoo-toimitusmaksut)
- ``stock`` (Odoo-varasto)

Tekijä ja tuki
==============

Tämän moduulin on kehittänyt `Webbros <https://webbros.fi>`_ — suomalainen Odoo-kumppani,
joka tarjoaa kehitys-, integrointi- ja tukipalveluita.

.. image:: static/description/webbros_logo.png
  :scale: 50%
  :target: https://www.webbros.fi/r/Eyq

Webbros Oy auttaa asiakkaita ottamaan käyttöön ja soveltamaan Odoo ERP-ratkaisua
oman toimintansa tehostamiseen ja automatisointiin. Webbros voi toimittaa Odoon
avaimet käteen -ratkaisuna tai auttaa pelkästään haastavimmissa osioissa
– asiakkaan toiveiden mukaan. Palveluihimme kuuluvat liiketoimintaprosessien suunnittelu
ja kehittäminen (BPR), ERP-tuotteen konfigurointi, tekniset toteutukset, integraatioiden rakentaminen,
raportoinnissa avustaminen, koulutukset, tuote- ja muun tiedon hallinta ja tuonti järjestelmään
sekä tuki ja ongelmanratkaisu projektin aikana ja sen jälkeen.


- **Verkkosivusto:** https://webbros.fi
- **Integroitu palvelu:** `Kuormat <https://kuormat.com>`_

Lisenssi
========

GPL-3

-----------------------
🇬🇧 In English
-----------------------

Overview
========

**Delivery Kuormat** is an Odoo delivery carrier integration that connects Odoo's
inventory and sales workflows to the `Kuormat <https://kuormat.com>`_ shipping platform.

.. image:: static/description/kuormat_com_logo.png
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
2. Set the *Provider* to **Delivery Kuormat**.
3. Enter your **Customer ID** and **API Key**, available in Kuormat.com profile settings.
4. Set default package dimensions and shipment type for automatic price calculations.

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

Author & Support
================

.. image:: static/description/webbros_logo.png
  :scale: 50%
  :target: https://www.webbros.fi/r/Eyq

This module is developed and maintained by `Webbros <https://webbros.fi>`_.
Webbros oy is Odoo official partner helping customers implement
and maintain their ERP operations in efficient way. We can provide Odoo
as turn-key solution, or simply help on the hard parts, depending on case.
Our services include business process re-design (BPR), configuration
of the product, technical implementations, building integrations,
helping with reporting, training and providing support and problem solving.


- **Website:** https://webbros.fi
- **Integrated service:** `Kuormat <https://kuormat.com>`_

License
=======

GPL-3
