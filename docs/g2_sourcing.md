# G2 off-board parts: sourcing and cost per build (2026-10-30)

Where to buy the parts that are not on the JLCPCB-assembled board, for a run of 5–10 frames ("builds"), and what each build costs including the board. Prices and stock were checked on 2026-10-30 (afternoon, Pacific time), for US delivery (Oakland). They will drift, so recheck at checkout. The board is ordered from JLCPCB ([`hardware.md`](hardware.md), ordering steps); its quotes are in [Assembled board (JLCPCB)](#assembled-board-jlcpcb).

Criteria, in order: quality and safety, price, the seller's reliability and support, then speed. The power bank is chosen on safety first.

## Chosen parts and cost per build

One build = one frame with one filament. Unit prices are at the quantity ordered for 10 builds.

| Part | Buy | Source | Qty per build | Unit price | Per build |
|---|---|---|---|---|---|
| Pot with switch (J2) | Same Sky **PTN09S1-H100115K1B** (100 k linear, SPST at the CCW end, 15 mm knurled shaft) | DigiKey 2223-PTN09S1-H100115K1B-ND (459 in stock) | 1 | $2.416 (10+) | $2.42 |
| Knob | Cliff **K21, 6 mm spline, CL178882** (push-on, Ø 19.3 × 19.2 mm) | DigiKey 4654-CL178882-ND (148 in stock) | 1 | $1.185 (10+) | $1.19 |
| Knob cap (sold separately) | Cliff **CL1730**, black | DigiKey (77 in stock) | 1 | $0.827 (10+) | $0.83 |
| Pot lead | Adafruit **4045**, JST-PH 4-pin socket to 200 mm wires | DigiKey 1528-2825-ND (498 in stock) | 1 | $0.95 | $0.95 |
| LED filament | DFRobot **FIT0926** (12 V, 600 mm, 2200 K) | DigiKey 1738-FIT0926-ND (328 in stock) | 1 | $5.90 | $5.90 |
| XIAO (U1) | Seeed **102010633**, XIAO ESP32C3 pre-soldered | Seeed Studio store (in stock, US warehouse) | 1 | $5.90 | $5.90 |
| Radar | Hi-Link **HLK-LD2410S**, "LD2410S Module" option | Hi-Link's own AliExpress store (2,077 available) | 1 | $4.55 | $4.55 |
| Radar shipping | AliExpress standard shipping, $5.58 per order, over 10 builds | | | | $0.56 |
| USB-C panel extension (bank input) | **FdcLixuvol 2-pack**, USB-C male to screw-mount female, 0.3 m, 2.5 A (B0GRVZ62VR) | Amazon (in stock) | 1 | $9.19 per 2 | $4.60 |
| Power bank | **CUKTECH PB200N**, 20,000 mAh 45 W, built-in USB-C cable, 162 × 72 × 29 mm (B0D8KH4LNB) | Amazon, sold by CUKTECH Direct (in stock) | 1 | $29.99 | $29.99 |
| Filament leads | BNTECHGO 22 AWG silicone wire, red and black, 25 ft each (B07HGT44XY), about 0.75 m of each per build | Amazon | 1/10 roll | $11.48 per roll | $1.15 |
| **Off-board parts per build** | | | | | **$58.02** |
| Assembled board | JLCPCB, 10 assembled boards, shipping and import duty included (DDP) | JLCPCB | 1 | $142.98 per 10 | $14.30 |
| **Total per build** | | | | | **$72.32** |

**Backup bank:** the **UGREEN Nexode PB536**, 20,000 mAh 45 W, built-in USB-C cable, 152 × 72 × 29 mm, Amazon B0DSPVDYQ9 (sold by UGREEN), $34.99, in stock. It adds $5.00, making a build **$77.32**.

**What the total leaves out:**
- tax and any tariff (DigiKey flags a possible tariff on Chinese-made parts, including the filament);
- shipping from DigiKey, Seeed and Amazon, shown at checkout (Seeed's free US shipping excludes XIAO orders);
- heat-shrink and solder.

**More filaments:** each one adds $5.90, plus a little wire. The board drives up to four ports, with strings up to 24 V total.

### Assembled board (JLCPCB)

These are the cart quotes from 2026-10-30, for project `fgl_g2-gerbers-jlcpcb_Y3`. The PCB is green, 1.6 mm, HASL (with lead); assembly is Economic PCBA, top side. The estimated ship date is 2026-10-31. Shipping is DDP, which includes import duty.

| | 5 boards | 10 boards |
|---|---|---|
| PCB (24 h build) | $3.05 (special offer) | $6.05 |
| Assembly, parts and fees (1–2 days) | $84.45 | $118.30 |
| Merchandise total | $87.50 | $124.35 |
| Shipping (DDP) | $31.89 | $38.63 |
| Coupons | −$16.00 | −$20.00 |
| **Subtotal** | **$103.39** | **$142.98** |
| **Per board** | **$20.68** | **$14.30** |
| Per board without the coupon | $23.88 | $16.30 |

- **The coupons** may be one-time new-customer coupons. If a later order doesn't get them, use the "without the coupon" row.
- **Ordering 10 instead of 5** costs $39.59 more for 5 more boards, about $7.92 each.

### Cost per build at 5 and 10 builds

Builds come in 5s, because JLCPCB's minimum is 5 boards. Each column is the total you would pay for that many builds, divided by the number of builds. It counts whole packs, the price breaks at that quantity and the board quote, with no spares.

| Part | 5 builds | 10 builds |
|---|---|---|
| Pot PTN09S1-H100115K1B (DigiKey breaks: 1+ $2.90, 10+ $2.416) | $2.90 | $2.42 |
| Knob CL178882 (5+ $1.27, 10+ $1.185) | $1.27 | $1.19 |
| Knob cap CL1730 (5+ $0.886, 10+ $0.827) | $0.89 | $0.83 |
| Pot lead Adafruit 4045 | $0.95 | $0.95 |
| Filament FIT0926 | $5.90 | $5.90 |
| XIAO 102010633 | $5.90 | $5.90 |
| Radar LD2410S | $4.55 | $4.55 |
| Radar shipping ($5.58 per AliExpress order) | $1.12 | $0.56 |
| USB-C panel extension (5: two 2-packs + one single B0FNQV23MY at $6.97; 10: five 2-packs) | $5.07 | $4.60 |
| Power bank CUKTECH PB200N | $29.99 | $29.99 |
| 22 AWG wire (one $11.48 roll, whatever the quantity) | $2.30 | $1.15 |
| **Off-board parts per build** | **$60.83** | **$58.02** |
| Assembled board, JLCPCB | $20.68 | $14.30 |
| **Total per build** | **$81.51** | **$72.32** |
| **Total spend** | $407.53 | $723.17 |
| Per build with the UGREEN PB536 backup bank (+$5.00) | $86.51 | $77.32 |

- **What changes with quantity:** mostly fixed costs, spread over more builds: the board order, the radar shipping and the wire roll.
- **What doesn't:** the bank is more than a third of every build and has no quantity discount.
- **The single cable** (B0FNQV23MY) is the same maker's one-piece listing; Amazon showed only 20 left.

### Order for 10 builds, with spares

The spares are 2 filaments (they are fragile), 2 XIAOs and 2 radars (ESD, bent pins).

| Vendor | Order | Total |
|---|---|---|
| DigiKey | 10 × PTN09S1-H100115K1B, 10 × CL178882, 10 × CL1730, 10 × Adafruit 4045, 12 × FIT0926 | $124.58 |
| Seeed Studio | 12 × 102010633 | $70.80 |
| AliExpress, Hi-Link store | 12 × LD2410S Module, plus $5.58 shipping | $60.18 |
| Amazon | 10 × CUKTECH PB200N, 5 × FdcLixuvol 2-packs, 1 roll BNTECHGO 22 AWG red/black | $357.33 |
| JLCPCB | 10 assembled boards (Economic PCBA, top side), shipping and duty included | $142.98 |
| **Total** | | **$755.87** (**$75.59 per build** including the spares) |

With the UGREEN PB536 instead, add $50.00 for 10 builds.

## Pot, knob and the recess

### Why this pot and knob

The prototype's knob needs a set screw, and a set screw can't be reached once the knob sits down in a recess. A **push-on** knob on a **knurled** shaft fixes that: mount the pot from inside, put the nut on from outside, and press the knob on.

- **PTN09S1-H100115K1B** decodes as 1 section, 100 kΩ, no detents, 15 mm shaft, K1 shaft (metal, 18-tooth knurl), B (linear) taper. It is a 9.5 mm pot with a rotary SPST switch (16 V DC, 3 A; switches within 50° of the CCW end), −10 to 75 °C, aluminium shaft. Its pins are PC pins: solder the lead's wires to them and sleeve each joint with heat-shrink.
- **Cliff K21 6 mm spline (CL178882):** Ø 19.3 mm at the skirt, 19.2 mm tall, 13.8 mm bore. The cap is a separate part. CL1730 is plain black; Cliff also makes a black cap with a marker line (CL1764), which shows the dimmer position (not checked at DigiKey).
- Alternative if you prefer solder lugs: Alpha **RV16A03F-10-15R1-B100K-0030** (Mouser, $3.20, 894 in stock). It is a 16 mm pot with a 15 mm *smooth* round shaft, so it needs a set-screw knob. In a recess that means pre-assembling the pot and knob on a small plate and fitting the plate from inside.

### Recess (20 mm frame wall)

Mount the pot body against the **inside** face of the wall. Everything is cut from the outside, and no counterbore is needed inside.

```
 outside                                   inside
   |<---------------- 20 mm wall ---------------->|
   |  Ø 23 pocket, 17.5 deep          | web 2.5 |  pot body (9.5 mm square, 12.2 deep)
 ==|==================================|=========|====
knob  ~6 mm proud                      nut+washer on the web, Ø 7.3 hole
```

| Feature | Size |
|---|---|
| Outer pocket | Ø 23 mm (knob skirt 19.3 + 1.8 mm clearance each side), 17.5 mm deep |
| Web left at the bottom of the pocket | 2.5 mm (the bushing is 5 mm: 2.5 web + 0.5 washer + 2 nut). Use 2.0 mm if your nut is thicker; drop the washer if needed |
| Bushing hole through the web | Ø 7.3 mm |
| Anti-rotation | If the bushing has a locating tab, drill a 1.5 mm blind hole for it in the inside face, or nip it off. The nut alone holds a pot this light |

**Where the knob ends up.** The knob's splined bore stops where the knurl starts, about 7 mm from the pot's mounting face (15 mm shaft, 8 mm of knurl). Its top is then 7 + 19.2 = 26.2 mm from the inside face, so it stands **about 6 mm proud** of the outside surface. This holds whatever the pocket depth, because the pot sits on the inside face. The skirt sits about 13 mm down in the pocket, so the protruding part is the knob's serrated top.

- **Want it lower?** Sand the knob's bottom face flat on sandpaper. Each millimetre removed lowers the knob by a millimetre, since its base still stops at the knurl. About 2 mm off gives roughly 4 mm proud.
- **The nut** is at the bottom of a Ø 23 mm pocket. A thin-wall socket or nut driver for the pot's nut (measure it: M7 nuts are usually 9–10 mm across flats) reaches it.
- **Wood under the nut:** 2–2.5 mm of hardwood or plywood is enough with gentle torque. A drop of thin CA glue soaked into the web stiffens it.
- **Check one before cutting ten.** Confirm the knurl length, the nut thickness and the knob's seating height with calipers on the first pot and knob, then set the pocket depth.

### Wiring the pot to J2

J2 (JST-PH 4-pin): 1 = GND (CCW end and switch common), 2 = wiper, 3 = CW end, 4 = switch.

| Adafruit 4045 lead | Pot pin |
|---|---|
| J2 pin 1 | pot pin 1 (CCW end), plus a short jumper to one switch pin (K1) |
| J2 pin 2 | pot pin 2 (wiper) |
| J2 pin 3 | pot pin 3 (CW end) |
| J2 pin 4 | the other switch pin (K2) |

Check with a meter before wiring: with the shaft fully CCW, pins 1–2 read about 0 Ω and K1–K2 are open; a few degrees clockwise, K1–K2 close. Adafruit's colour order is not a JST standard, so match the wire on each J2 pin by continuity, not by colour.

## LED filaments

**DigiKey, DFRobot FIT0926, $5.90, 328 in stock.** DFRobot's own store is cheaper ($5.70 each at 5+, $5.50 at 10+), but it ships from China. For 10–12 pieces DigiKey's US stock costs about $5 more and arrives in days. FIT0926 is rated 12 V 500 mA, 400 lm, −30 to +55 °C.

You also need hook-up wire from each filament to its port: 22 AWG stranded silicone, red and black, and heat-shrink for the joints at the filament tabs. Any reputable brand will do.

## XIAO ESP32C3

**Seeed 102010633, pre-soldered, $5.90 from Seeed's store** (US warehouse). The BOM listed 113991054 until today; that SKU has **no headers**, so the BOM, schematic and generator now say 102010633.

DigiKey lists 102010633 at $5.90 but had none in stock on 2026-10-30, with a restock date that had already passed.

Header length: standard 6 mm pins stop about 2 mm above the 5 mm sockets (D15). This is mechanical only; trim the pins if the height matters in the frame.

## Radar: HLK-LD2410S

**Hi-Link's own AliExpress store** ("Shenzhen Hi-Link Power & Radar & Router Module Store", 97.9 % positive), item 3256807802776152: $4.55 for the "LD2410S Module" option, standard shipping about $5.58 per order, delivery about 1–2 weeks, free returns within 90 days. Buying from the maker's own store avoids relabelled or counterfeit modules. Many other listings show $1.09, but that is a new-shopper teaser price.

- Pick **"LD2410S Module"**, not "KIT". The kit adds bench accessories; at most one is useful, for configuring a module from a PC.
- J3 expects a 1 × 5, 2.54 mm male header. If the photos or the delivered modules have no pins, solder a 1 × 5 2.54 mm header (the same 6 mm pin-length note as the XIAO applies).
- Plan for the slower delivery: order the radars first.

## USB-C panel extension (frame inlet to the bank's input)

In the prototype this cable only charges the bank: the bank's own built-in cable feeds the board. It carries power only, so data speed doesn't matter. It must pass CC, though: a USB-C charger supplies nothing until it sees the bank's Rd through the cable. So it has to be a real USB-C male-to-female extension, not a 2-wire "charge-only" pigtail. Every listed extension below is a full USB-C cable.

There is no cheap "USB 2.0, power only" version from a known brand. The panel-mount types all come from small generic makers, and the USB 3.x builds are the common, cheapest ones. The distributor versions (Adafruit 4218, SparkFun 15455, Switchcraft) cost $12–60.

| Cable | Price each | Notes |
|---|---|---|
| **FdcLixuvol 2-pack, B0GRVZ62VR** (chosen) | $4.60 ($9.19 per 2) | 0.3 m, screw-ear female with 17 mm screw spacing, rated 2.5 A, 3 reviews. Same maker sells singles (B0FNQV23MY, $6.97, 11 reviews, 4.6) |
| Seadream B0BHKQMB73 | $6.99 | Rated 3 A; looks like the AAOTOKK head; no reviews |
| AliExpress (e.g. HOQO store, 4.9, 500+ sold) | $4.70–6.10 + about $5.90 shipping | No saving at 10 pieces once shipping is added |
| AAOTOKK B08HS6X44P (prototype) | $9.69 | 3 A, 148 reviews; the fallback if a FdcLixuvol cable fails the check below |

**2.5 A is enough.** A cable without an e-marker limits a PD charger to 3 A anyway. The PB200N and PB536 take at most 40 W (20 V × 2 A, or 15 V × 2.6 A).

**Check each cable once.** With generic cables, check that each one passes CC and current before it goes in a frame. Plug a USB-C PD charger into the panel end and the bank into the other, then confirm the bank shows fast charging (most have a display or a fast-charge indicator). An inline USB-C power meter, about $20–30, makes this quick and is useful for G2-T15 too.

## Power bank

### What the market offers

- **25–30 Ah:** reputable brands only make these as 100–200 W "laptop" banks, so they cost $50–105. The cheapest, the EcoFlow RAPID 25K ($50.99), is a 49 mm-thick brick. The slim ones (≤ 30 mm) start at about $70.
- **20 Ah:** basic banks with USB-C in and out from established brands cost $27–35 and are 28–30 mm thick.
- **Under $30 at 25–30 Ah:** only unknown brands, which you ruled out.

### Chosen: CUKTECH PB200N, 20,000 mAh 45 W, built-in USB-C cable

Amazon B0D8KH4LNB, sold by CUKTECH Direct, $29.99, 4.6 stars from 3,900 ratings. Best Buy also stocks it.

- **Shape and ports.** 162 × 72 × 29 mm and about 500 g. It has a built-in USB-C cable (input and output) to feed the board, as in the prototype, plus a USB-C port (input and output) for the panel inlet and a USB-A port. Input is 40 W max.
- **Capacity.** 74 Wh rated. A test measured 80–91 % of rated capacity: roughly 59–67 Wh, about what the 25 Ah UGREEN gave at 5 V 1 A (65 Wh).
- **Maker.** CUKTECH merged with ZMI, a company in Xiaomi's ecosystem, and makes power banks for Xiaomi, LG and Hitachi. That comes from a sponsored article, so treat it as the company's own account. The listing claims UL, CE, CB and FCC certification and a 24-month warranty.
- **Low-current shut-off.** The listing says output stops after 30 s at low current, unless its trickle mode is on, and trickle mode lasts only 2 h. The board's keep-alive pulses 152 mA for 200 ms every 10 s (D11), which should hold it on. G2-T15 (b) must confirm this.

**Runtime with 20 Ah instead of 25** (`power_model.py`, one 12 V filament at 150 mA): 7.2 days at 4 h/day instead of about 9 days. In manual mode it is about 29 h continuous instead of about 36 h. Requirement 4 already allows 20–30 Ah banks.

### Backup: UGREEN Nexode PB536, 20,000 mAh 45 W, built-in USB-C cable

Amazon B0DSPVDYQ9, sold by UGREEN, $34.99, 4.5 stars from 4,800 ratings.

- Same layout as the PB200N: a built-in USB-C cable for input and output, a USB-C port and a USB-A port.
- 152 × 72 × 29 mm and 468 g.
- From UGREEN, the better-known brand. Use it if the PB200N fails G2-T15 or is out of stock.

### Also considered

| Bank | Price | Size | Why not |
|---|---|---|---|
| INIU 20,000 mAh 22.5 W (P512), B0FX7T4H7D | $26.95 | 104 × 71 × 28 mm | Cheapest and smallest (built-in USB-C lanyard cable, 4.6 stars from 28,800 ratings), but INIU recalled an older model (BI-B41, sold 2021–22) in December 2025 |
| CUKTECH 25,000 mAh 100 W, built-in cable (LPB252N), B0GHHDV7Y9 | $69.99 | 160 × 80 × 27 mm | The cheapest slim 25 Ah from a known brand: $40 more for 25 % more capacity |
| UGREEN Nexode 25,000 mAh 165 W, built-in cables (PB552), B0DSPX4RQ5 | $74.99 | 169 × 81 × 27 mm | The first pick; more than needed |
| EcoFlow RAPID 25,000 mAh 170 W, B0FHPMX7DR | $50.99 | 157 × 54 × 49 mm | Far too thick |
| Anker Zolo 20K 30W (A1689), B0CZ9LH53B | $35.99 | 120 × 73 × 31 mm | This model number was in Anker's 2025 recall (units sold August 2023 to June 2025) |
| Belkin BPB012 20K, B09NTNTVRJ | $29.00 | 154 × 77 × 22 mm | The thinnest, but its USB-C port gives only 15 W shared, so recharging is slow |
| AONIDI AC-02DP (the prototype's bank, B0DQPD24ZD) | $37.99 | | Not an established battery brand |

### Recall context

Recalls are not a reason to rule a brand out. In 2025 Anker recalled about 1.1 million PowerCore 10000 units (A1263), and later about 481,000 more across five small models (A1647, A1652, A1257, A1681, A1689). INIU recalled about 210,000 BI-B41 units. My searches found no US recall of a UGREEN, EcoFlow or CUKTECH power bank. Xiaomi, CUKTECH's partner, recalled 146,891 PB2030MI banks (its own model). Neither the PB200N nor the PB536 is a recalled model.

### Using a bank inside a frame (safety)

These matter more than the brand choice:

1. **Temperature.** Anker's A1695 safety sheet gives an operating range of 0–35 °C. UGREEN and EcoFlow don't publish one for these models, but Li-ion banks are similar. The board's design corner is a 55 °C closed frame (D12), well above that.
   - Mount the bank low in the frame and not touching the board.
   - Give the back panel vent slots at the top and bottom.
   - Measure the bank's temperature in the closed frame (G2-T15).
2. **Charging.** Charge it, then unplug: don't leave a charger on the panel inlet all the time. Anker's sheet warns against leaving its bank on the charger long after it is full, and Li-ion ages fastest when kept full and warm.
3. **Pass-through.** What happens when a charger is plugged in while the lamp is on varies by bank. Some briefly cut their output while they renegotiate, which would reset the board. G2-T15 checks this.
4. **Low-load shut-off.** Laptop banks switch off at low current after a while. The board's keep-alive pulses (D11) are meant for this. Confirm it with the chosen bank, at idle and at the lowest dim setting.
5. **Inspect and replace.** If a bank swells, runs hotter than before or charges slowly, retire it. Register the banks with the maker so you hear about any recall.
6. **Shipping a frame with the bank inside.** That counts as a lithium-ion battery packed in equipment (UN3481). All the banks here are under 100 Wh (74 Wh for the CUKTECH), which keeps them in the simpler shipping category, but carriers have packing and labelling rules.

Hardware.md requirement 4 lets an owner fit their own 20–30 Ah bank. Selling frames without a bank, with a list of tested banks, would take $30 (about half) off each build.

## Order plan for 10 builds

1. **AliExpress, Hi-Link store:** 12 × LD2410S Module. It has the longest lead time, so order it first.
2. **Amazon, first:** 1 × CUKTECH PB200N and 1 × FdcLixuvol 2-pack. Run G2-T15 with them and check both cables (see the USB-C panel extension section) before ordering the rest.
3. **DigiKey:** 10 × PTN09S1-H100115K1B, 10 × CL178882, 10 × CL1730, 10 × Adafruit 4045 and 12 × FIT0926. Only 77 CL1730 caps were in stock.
4. **Seeed Studio:** 12 × 102010633.
5. **Amazon, the rest:** 9 × PB200N (or PB536), 4 × FdcLixuvol 2-packs and 1 roll of BNTECHGO 22 AWG red/black.
6. Build one frame end to end before cutting the other nine recesses.

## Sources

- DigiKey product pages (2026-10-30): PTN09S1-H100115K1B https://www.digikey.com/en/products/detail/same-sky-formerly-cui-devices/PTN09S1-H100115K1B/24767790, CL178882 https://www.digikey.com/en/products/detail/cliff-electronic-components-ltd/CL178882/26698218, CL1730, Adafruit 4045 https://www.digikey.com/en/products/detail/adafruit-industries-llc/4045/9843408, FIT0926 https://www.digikey.com/en/products/detail/dfrobot/FIT0926/20500163, 102010633
- Same Sky PTN09SX datasheet: https://www.sameskydevices.com/product/resource/ptn09sx.pdf
- Cliff K21 knob datasheet: https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/6822/Knob%20K21.pdf
- Mouser, Alpha RV16A03F-10-15R1-B100K-0030 (checked 2026-10-29)
- Seeed XIAO ESP32C3 pre-soldered (102010633), Seeed store: https://www.seeedstudio.com/Seeed-Studio-XIAO-ESP32C3-Pre-Soldered-p-6331.html; SKU confirmation: https://www.pakronics.com.au/products/seeed-studio-xiao-esp32c3-pre-soldered-ss102010633
- Hi-Link LD2410S, Hi-Link's AliExpress store: https://www.aliexpress.us/item/3256807802776152.html
- Panel-mount USB-C extensions: FdcLixuvol https://www.amazon.com/dp/B0GRVZ62VR and https://www.amazon.com/dp/B0FNQV23MY; Seadream https://www.amazon.com/dp/B0BHKQMB73; AAOTOKK https://www.amazon.com/dp/B08HS6X44P; HOQO (AliExpress) https://www.aliexpress.us/item/3256803301707138.html
- CUKTECH PB200N: https://www.amazon.com/dp/B0D8KH4LNB; test: https://techtest.org/cuktech-pb200n-preiswerte-powerbank-mit-usb-c-45w-und-pps; company background (sponsored): https://www.androidauthority.com/cuktech-power-banks-3446893
- UGREEN PB536 (backup): https://www.amazon.com/dp/B0DSPVDYQ9; BNTECHGO 22 AWG wire: https://www.amazon.com/dp/B07HGT44XY; Belkin BPB012: https://www.amazon.com/dp/B09NTNTVRJ; INIU P512: https://www.amazon.com/dp/B0FX7T4H7D; CUKTECH LPB252N: https://www.amazon.com/dp/B0GHHDV7Y9; Anker Zolo A1689: https://www.amazon.com/dp/B0CZ9LH53B
- UGREEN PB552: https://www.amazon.com/dp/B0DSPX4RQ5; capacity test: https://techtest.org/ugreen-nexode-power-bank-25000-mah-165w-im-test-viel-leistung-zum-fairen-preis/
- EcoFlow RAPID 25K: https://www.amazon.com/dp/B0FHPMX7DR; Anker A1695: https://www.amazon.com/dp/B0DCBB2YTR; INIU P63: https://www.amazon.com/dp/B0GJ7ZWGJ3
- Anker A1695 safety sheet (0–35 °C): https://lp.ankerjapan.com/hubfs/aoos/manual/A1695Safety.pdf
- Anker A1695 pass-through: https://service.anker.com/article-description/Understanding-Pass-Through-Charging-in-Anker-Power-Bank-165W-Built-In-and-Retractable-Cables
- Anker recall (481,000 units): https://www.ktvu.com/news/anker-power-bank-recall-fire-hazard
- 2025 recalls and the cell supplier: https://www.notebookcheck.net/Anker-Romoss-Baseus-face-massive-power-banks-recalls-over-safety-risks.1041335.0.html
- INIU BI-B41 recall: https://www.14news.com/2025/12/10/power-banks-sold-amazon-recalled-after-reports-fires-burn-injuries
