# Fused Glass Lighting — Hardware (Rev F)

Presence-activated, pot-dimmed backlighting for a fused glass piece. Two 30 cm 3 V LED
filaments driven at **300 mA each** by linear constant-current modules, gated by a 24 GHz
presence radar, running from a **25,000 mAh USB powerbank**.

Firmware: [`../src/main.c`](../src/main.c). Previous iteration archived at
[`archive/main_previous_iteration.c.txt`](archive/main_previous_iteration.c.txt).

---

## 1. What changed from the previous iteration

The last build was a MOSFET chopping resistor-ballasted filaments at 100 mA from a wall
supply. Four things forced a redesign.

| Was | Now | Why |
|---|---|---|
| XYC-WB-DC Doppler radar | **HLK-LD2410S** | Doppler cannot see a person standing still. Fatal for a lamp someone stands in front of to look at the artwork. |
| MOSFET + 22 Ω ballast, ~100 mA | **CN5711 CC modules, 300 mA** | Needs to be bright enough to backlight glass. Current stays constant as the cell sags. |
| 5 kHz PWM | **1 kHz PWM** | The CN5711 CE pin is specified below 2 kHz. |
| Wall PSU | **25,000 mAh powerbank** | Cordless placement. Brings the auto-shutoff problem with it. |
| 60 s off-delay | **25 s** | Battery, not mains. |

---

## 2. Parts

Passive values are drawn from assortment kits already on hand — see §2.1 for the mapping.
Prices verified August 2026.

### Still to buy

| Qty | Part | Amazon | Notes |
|---:|---|---|---|
| 1 | Seeed XIAO ESP32-C3 | [B0B94JZ2YF](https://www.amazon.com/dp/B0B94JZ2YF) — $9.90 | ESP-IDF via PlatformIO |
| 2 | 3 V LED filament, 300 mm, 2200–2700 K | [B0CV83D25S](https://www.amazon.com/dp/B0CV83D25S) — $9.49 | jojofuny 4-pack; you need 2, spares are welcome |
| 1 | HLK-LD2410S 24 GHz radar | [B0DBSKL6BC](https://www.amazon.com/dp/B0DBSKL6BC) — $9.99 | **Must be the "S" variant.** See warning below |
| 1 | Ceramic capacitor kit | [B07P8N8BW9](https://www.amazon.com/dp/B07P8N8BW9) — $12.99 | BOJACK. 100 nF confirmed present |
| 1 | Electrolytic capacitor kit | [B07PBQXQNQ](https://www.amazon.com/dp/B07PBQXQNQ) — $16.99 | BOJACK. 10 µF confirmed present |
| 1 | 2N7000 N-channel MOSFET, TO-92 | [B083TF4K6L](https://www.amazon.com/dp/B083TF4K6L) — $8.99 | 100-pack. See §6 on gate drive |
| 1 | 1N5819 Schottky diode, DO-41 | [B079KG1TN2](https://www.amazon.com/dp/B079KG1TN2) — $7.99 | 100-pack |
| 1 | ElectroCookie solderable breadboard | [B07ZYPCXZ3](https://www.amazon.com/dp/B07ZYPCXZ3) — $18.99 | 9-pack + 3 mini; a 5-pack exists cheaper |
| 1 | Powerbank, 25,000 mAh | [B0DCBB2YTR](https://www.amazon.com/dp/B0DCBB2YTR) — $104.99 | Anker. USB-A port confirmed in specs |
| 1 | Silicone hookup wire, 22 AWG stranded | [B089CQHRDT](https://www.amazon.com/dp/B089CQHRDT) — $12.29 | Fermerry, 6 colors |
| 1 | Dupont jumper wire kit | [B01EV70C78](https://www.amazon.com/dp/B01EV70C78) — $6.98 | ELEGOO, M-M / M-F / F-F |

Capacitors are the only passive gap the kits on hand do not fill.

### Already on hand

| Qty | Part | Amazon | Role |
|---:|---|---|---|
| 2 | CN5711 constant-current driver module | [B0F1K97V61](https://www.amazon.com/dp/B0F1K97V61) | 2-pack. Listing since retitled generically; see §3 |
| 1 | USB-C PD trigger module | [B0D7CFSCP6](https://www.amazon.com/dp/B0D7CFSCP6) | AITRIP. **Read §8 before wiring** |
| — | Chanzon 2 W ±1% metal film kit, 30 values | [B08QR72BFW](https://www.amazon.com/dp/B08QR72BFW) | Supplies 4.7 Ω and 33 Ω |
| — | BOJACK 1/2 W ±1% metal film kit, 25 values, 1000 pcs | [B08FHPJ5G8](https://www.amazon.com/dp/B08FHPJ5G8) | Supplies 100 Ω, 470 Ω, 4.7 k, 5.6 k, 100 k |
| — | BOJACK 6 mm trimmer potentiometer kit, 15 values | [B07WHJMVR4](https://www.amazon.com/dp/B07WHJMVR4) | Supplies the 10 kΩ brightness pot — see §2.2 |
| — | JuForAcc 10 W cement resistor kit, 25 values | [B0FH4STPP7](https://www.amazon.com/dp/B0FH4STPP7) | **Not used in the build.** Bench load ladder for step 2 of §11 |

**Radar warning.** Several Amazon listings put "LD2410S" in the title while actually
shipping an LD2410B or LD2410C. Those draw ~80 mA against the S variant's 0.45 mA — 175×
the idle budget, which would collapse runtime from days to hours. Check the photos for the
"S" marking on arrival and measure idle current before committing it to the board.

**Powerbank note.** Most 25,000 mAh banks are now USB-C-only PD laptop banks. The Anker
above is listed with 3× USB-C plus 1× USB-A. An INIU alternative
([B08VDJP7WN](https://www.amazon.com/dp/B08VDJP7WN), ~$60) also confirms a USB-A port but
was showing low stock. If you already own a suitable bank, use it — capacity is the only
spec that matters here.

**Do not reuse** the XYC-WB-DC or the FQP30N06L from the previous build. The power MOSFET
is replaced by the driver modules' own CE inputs.

### 2.1 Resistor value mapping

Every fixed value below comes from a kit already on hand. Note that the BOJACK 1/2 W kit
jumps 2.2 k → 4.7 k → 5.6 k → 7.5 k with **no 3.3 k, 3 k, or 2.7 k**, which is what drives
the combinations chosen here.

| Value | Qty | Where it goes | Source |
|---|---:|---|---|
| 5.6 kΩ + 470 Ω in series | 2 pairs | RISET — 6.07 kΩ, see §3 | 1/2 W kit |
| 4.7 Ω | 2 | Filament ballast | 2 W kit |
| 33 Ω | 1 | Keep-alive dummy load | 2 W kit |
| 4.7 kΩ | 1 | Pot divider top leg — see §2.2 | 1/2 W kit |
| 100 Ω | 1 | MOSFET gate series | 1/2 W kit |
| 100 kΩ | 1 | MOSFET gate pulldown | 1/2 W kit |
| 10 kΩ | 1 | CE net failsafe pulldown — see §9 | 1/2 W kit |

The CE pulldown wants to be stiff enough to beat two CN5711 internal pull-ups in parallel.
10 kΩ is the target; if the kit turns out not to carry it, **4.7 kΩ is confirmed present**
(it is the pot divider top leg) and works at least as well here. Do not substitute 100 kΩ
to match the MOSFET gate pulldown — against an unknown internal pull-up that can land the
net mid-rail, which is the one outcome worse than either extreme.

1/2 W parts are oversized for the signal-level positions — RISET dissipates well under a
milliwatt — but they are what is in the drawer and they fit the board fine.

### 2.2 Brightness pot and the ADC divider

The pot is wired as a **divider with a fixed top leg**, not as a bare series resistor into
the ADC pin:

```
3V3 ──► 4.7 kΩ ──► pot pin 3 (CW)
                   pot pin 2 (wiper) ──► D1     (100 nF from D1 to GND)
                   pot pin 1 (CCW)   ──► GND
```

The top leg is what keeps the wiper inside the ESP32-C3's usable ADC range. With 4.7 kΩ
above a 10 kΩ pot the wiper tops out at

\[ 3.3 \times \frac{10}{14.7} = 2.25\ \text{V} \]

comfortably below the ~2.5 V point where the C3's ADC goes non-linear. A series resistor
between wiper and pin would attenuate nothing, since the ADC input is high-impedance — an
earlier revision of this document had it wired that way and was wrong.

2.2 kΩ + 1 kΩ = 3.2 kΩ gives 2.50 V instead if you want to use more of the ADC range. It
does not matter much: `ADC_RAW_AT_MAX` is calibrated from a measurement anyway (§11 step 8),
and 2.25 V still leaves roughly 2960 counts across the knob's travel.

**Do not expect 2.25 V to land at 2.25/3.3 × 4095 ≈ 2790.** Under `ADC_ATTEN_DB_12` the
C3's effective full scale is about **3.1 V**, not the 3.3 V rail, so the count works out at
2.25/3.1 × 4095 ≈ 2970 — which is where the ~2960 figure comes from, and why a reading near
2950 is correct rather than 6% high. The measured value on this build is 2950.

**On using a trimmer.** The kit on hand supplies 6 mm PCB trimmers, not panel-mount knob
pots. Electrically they are fine — ±20% tolerance is irrelevant in a ratiometric divider,
and 0.1 W against 0.8 mW of real dissipation is no constraint. The difference is
ergonomic: a trimmer is a screwdriver adjustment you set once at installation and cannot
knock out of place afterward, which for a fixed art piece is arguably the better behaviour.
If you want a knob a viewer can turn, fit a [WH148 panel
pot](https://www.amazon.com/dp/B07B64MWRF) instead. The trimmer listing does not state its
taper; small trimmers are near-universally linear, but if brightness tracks strangely
across the travel, that is the thing to check.

The divider draws ~0.22 mA continuously from 3V3, about 4% of the idle budget in §5.

---

## 3. Setting the drive current

The CN5711 sets LED current from a single resistor to ground:

```
I_LED = 1800 / R_ISET        (amps, ohms)
300 mA  ->  6.0 kΩ
```

**6.04 kΩ is an E96 value and is stocked in no through-hole assortment kit** — the only
Amazon source found was a 1206 SMD part, useless on a solderable breadboard. Build it from
values on hand instead:

| Combination | Total | Resulting current | Notes |
|---|---|---|---|
| **5.6 kΩ + 470 Ω** | **6.07 kΩ** | **296.5 mA** | **Chosen.** Two parts, 1.2% under target |
| 2 kΩ × 3 | 6.00 kΩ | 300.0 mA | Exact, three parts |
| 4.7 kΩ + 1 kΩ + 330 Ω | 6.03 kΩ | 298.5 mA | |

5.6 kΩ plus a trim resistor is also the most convenient starting point for calibration,
because the kit gives you 100, 120, 150, 220, 330, 470 and 1 k to walk the value in with,
forty of each.

**Verify empirically before trusting the formula.** The datasheet floor is 60 mA but the
module listing advertises 28 mA minimum, which suggests the boards may ship a variant with
a different constant. The listing has also since been retitled generically with no mention
of "CN5711" anywhere, so the chip on your revision is not guaranteed. Fit the resistors,
measure actual filament current with a meter in series, and swap the trim value to suit.

### Why 300 mA

| Drive current | Filament surface | Est. junction | Verdict |
|---|---|---|---|
| 100 mA | 32 °C | ~47 °C | previous build — dim |
| **300 mA** | **45 °C** | **~60 °C** | **chosen** |
| 500 mA | 58 °C | ~73 °C | ceiling for longevity |
| 1000 mA | 87 °C | ~102 °C | do not |

Keeping the junction under 85 °C is the condition for roughly 30,000 h to 90% surviving
flux.

Dimming to save battery does not work — total light energy per charge is flat within 7%
across a 3× brightness range, because efficacy droop cancels the runtime gain. Run it
bright and save power by shortening the off-delay instead.

---

## 4. Ballast resistors — the thermal trap

The CN5711 is a **linear** regulator in a SOP8 with **θJA = 300 °C/W**. It begins folding
back LED current at a 135 °C junction, which allows only **367 mW per package**.

Dropping 5 V to a 2.8 V filament at 300 mA burns 660 mW — nearly double the budget. The
failure mode is nasty: no shutdown, no error, the lamp just quietly dims over the first few
minutes and never reaches the brightness you set. The fix is to move most of that heat into
a resistor that can survive it.

| Ballast | Dissipated in IC | Junction temp | In the resistor |
|---|---|---|---|
| none | 660 mW | 223 °C — **throttles** | — |
| 3.9 Ω | 309 mW | 118 °C — ok | 351 mW |
| 4.3 Ω | 273 mW | 107 °C — ok | 387 mW |
| **4.7 Ω** | **237 mW** | **96 °C — ok** | **423 mW** |

**Use 4.7 Ω.** Best margin on the IC, standard E24 value, and the 2 W parts in the kit give
4.7× headroom. Regulator headroom stays at 0.79 V against a ~75 mV dropout at 300 mA, so
regulation holds even if the rail sags to 4.8 V.

This does not improve efficiency. Linear is linear; the supply still draws 300 mA per
channel. The resistor only relocates heat.

**One resistor per filament, never shared.** Vf mismatch between two parallel filaments
makes one hog current and fail early.

---

## 5. Power budget and runtime

A 25,000 mAh bank holds 92 Wh at the cell; after the boost to 5 V at ~90% you have
**16,650 mAh usable at 5 V**.

| State | Draw |
|---|---:|
| **On** — 2 × 300 mA + XIAO (25 mA) + LD2410S | **625.5 mA** |
| **Idle** — light sleep + LD2410S + keep-alive + pot divider | **~5.9 mA** |

| Usage | Per charge |
|---|---:|
| Continuous | 26.6 h |
| 2 h/day | 12.1 days |
| **4 h/day** | **6.4 days** |
| 8 h/day | 3.3 days |

Idle is negligible against the on-state, so runtime is set almost entirely by lit hours.
The PD trigger module adds its own quiescent draw (typically 1–5 mA) on top of the idle
figure — measure it, because at ~6 mA baseline it is not a rounding error.

---

## 6. Powerbank keep-alive

Powerbanks shut down when they think nothing is plugged in — typically below **45–100 mA
sustained for 15–60 s**. Idle draw here is under 1 mA, so without intervention the bank
powers down a minute after the lamp goes dark and never wakes.

Vendor trickle modes do not solve this: Anker's requires 30–90 mA and **auto-deactivates
after 2 hours**; Aukey's expires after four.

**Test this before you build it.** A live USB-PD contract holds the CC lines active, and
some banks keep the port powered as long as a PD sink is negotiated. If your bank behaves
that way with the trigger module attached, the entire keep-alive circuit becomes
unnecessary and you get the 3 mA back. Do not assume it — leave the lamp dark for an hour
with just the trigger connected and see whether the rail survives.

If it does not, build the circuit: N-channel logic-level MOSFET, gate to `D10` through
100 Ω, 100 kΩ gate pulldown, drain through **33 Ω 2 W** to +5 V, source to ground.

Firmware pulses it 200 ms every 10 s while dark. Tuning:

| Pulse | Average | Cost per 20 h idle |
|---|---:|---:|
| 100 ms / 10 s | 1.5 mA | 0.03 Ah |
| **200 ms / 10 s** | **3.0 mA** | **0.06 Ah** |
| 300 ms / 10 s | 4.6 mA | 0.09 Ah |

If the bank still sleeps, **lengthen the pulse before shortening the period** — reliable
detection matters more than frequency. Constants live at the top of `main.c`.

**Gate drive caveat.** The 2N7000 is specified at Vgs = 4.5 V, but the XIAO drives 3.3 V.
Rds(on) will be higher than datasheet-typical — expect roughly 8–15 Ω instead of ~5 Ω, so
the pulse draws closer to 110–120 mA than the ideal 152 mA. Still comfortably above the
shutoff threshold, but **measure the actual pulse current**; if it lands under about
100 mA, drop the 33 Ω to 22 Ω.

---

## 7. Pin assignments

| Signal | XIAO | GPIO | Peripheral |
|---|---|---|---|
| Potentiometer wiper | `D1` | GPIO3 | ADC1 channel 3 |
| Driver CE (both modules) | `D2` | GPIO4 | LEDC ch0, **1 kHz**, 13-bit, XTAL clock |
| Radar OT2 | `D3` | GPIO5 | digital in, pulldown, **light-sleep wake** |
| Radar RX (optional) | `D4` | GPIO6 | UART TX — config only |
| Radar TX (optional) | `D5` | GPIO7 | UART RX — config only |
| Keep-alive gate | `D10` | GPIO10 | digital out |

Constraints that produced this map:

- **Only D0–D3 can wake from light sleep.** The radar has to be one of them.
- **Only A0/A1/A2 (GPIO2/3/4) are on ADC1.** Seeed documents A3/GPIO5 (ADC2) as
  unreliable, so the pot must sit on ADC1.
- **D0 (GPIO2), D8 (GPIO8), D9 (GPIO9) are strapping pins.** Leave unconnected.
- **Do not put the radar UART on D6/D7.** Those are GPIO21/GPIO20 = U0TXD/U0RXD; the boot
  log emerges from GPIO21 and would be injected into the sensor's RX pin on every reset.

Putting the radar on D3 is the move that makes it all fit: it only needs a logic level, so
GPIO5's ADC2 problem is irrelevant, and ADC1 stays free for the pot.

The UART is only needed to tune LD2410S sensitivity and range. Normal operation runs
entirely off OT2, so you can omit `D4`/`D5` once the sensor is configured.

---

## 8. Power entry — the PD trigger module

The chosen module is an **AITRIP USB-C PD/QC trigger (decoy) board**, not a plain 5 V
breakout. It negotiates a power contract with the source and outputs the negotiated
voltage, selectable between **5 V / 9 V / 12 V / 15 V / 20 V** at up to 5 A, with a button
lock to prevent accidental changes.

That capability is the hazard.

> ### Set it to 5 V and engage the button lock before it ever touches the circuit.
>
> The CN5711 modules are rated **2.9–6.1 V input**. The XIAO's `5V` pin expects USB VBUS.
> A stray press selecting 9 V — never mind 20 V — destroys both driver modules, both
> filaments, and the XIAO instantly and simultaneously. There is no protection anywhere in
> this design against an over-voltage supply, because nothing in the original plan could
> produce one.

**Bench-verify before soldering anything:**

1. Plug the trigger into the powerbank on its own. Meter the output. Confirm **5.0 V**.
2. Engage the button lock.
3. Unplug and replug five times. Confirm it comes back at 5 V every time and never
   transiently higher. A trigger that defaults to a higher voltage on power-up is unusable
   here.
4. Leave it connected and idle for an hour to see whether the PD contract keeps the bank
   awake (see §6).

**Check the output form factor.** This ASIN ships in several variants. The one indexed as
default outputs to a **Type-C female socket**, which cannot be wired to a breadboard. You
need the variant with **solder pads or screw terminals**. If you received the socket
version, you will also need a USB-C female breakout to land the rail on the board.

### Wiring the rail

Trigger module output `+` → `+5V` rail, output `−` → `GND` rail. From there:

- Both driver modules' `VIN` and the keep-alive resistor tap the `+5V` rail directly.
- The XIAO's `5V` pin is fed from the rail **through the 1N5819 Schottky** (anode to rail,
  cathode to pin). The XIAO's `5V` pin is a USB *output*, and Seeed's documentation
  requires the diode when back-feeding it. This also leaves the XIAO's own USB-C free for
  flashing without contention.

Tie all grounds to a single star point at the power entry.

---

## 9. Point-to-point wiring

Filament polarity: the **positive** tab has a small hole punched in it.

| From | To | Notes |
|---|---|---|
| Powerbank USB-A or USB-C | PD trigger input | set to 5 V, locked |
| trigger `+` out | `+5V` rail | |
| trigger `−` out | `GND` rail | |
| `+5V` rail | 1N5819 anode | |
| 1N5819 cathode | XIAO `5V` | |
| XIAO `GND` | `GND` rail | |
| XIAO `3V3` | `+3V3` node | quiet local rail |
| `+3V3` node | 4.7 kΩ → pot pin 3 (CW end) | divider top leg — **not** in the wiper line |
| pot pin 1 (CCW end) | `GND` rail | |
| pot pin 2 (wiper) | XIAO `D1` | 100 nF from the `D1` node to GND |
| `+3V3` node | radar VCC | 100 nF + 10 µF at the module |
| radar GND | `GND` rail | |
| radar OT2 | XIAO `D3` | 3.3 V logic, no shifter |
| radar RX | XIAO `D4` | optional |
| radar TX | XIAO `D5` | optional |
| `+5V` rail | driver 1 `VIN`, driver 2 `VIN` | 10 µF at each |
| driver 1 `ISET` | 5.6 kΩ + 470 Ω series → `GND` rail | 6.07 kΩ total |
| driver 2 `ISET` | 5.6 kΩ + 470 Ω series → `GND` rail | 6.07 kΩ total |
| XIAO `D2` | driver 1 `CE` **and** driver 2 `CE` | one net, both modules |
| CE net | 10 kΩ → `GND` rail | **failsafe pulldown — see below** |
| driver 1 `LED+` | 4.7 Ω 2 W → filament A **+** | |
| driver 2 `LED+` | 4.7 Ω 2 W → filament B **+** | |
| filament A **−**, filament B **−** | respective driver `LED−` | keep the two loops separate |
| XIAO `D10` | 100 Ω → MOSFET **G** | 2N7000, TO-92 |
| MOSFET **G** | 100 kΩ → **S** | pulldown, stops the load latching on at reset |
| MOSFET **S** | `GND` rail | |
| MOSFET **D** | 33 Ω 2 W → `+5V` rail | |

2N7000 in TO-92, viewed from the **flat face**, pins left to right: **S, G, D**. Note this
is a different order from the FQP30N06L used in the previous build — check before
soldering.

**The CE pulldown is not optional.** The CN5711 modules pull `CE` up internally, so an
undriven CE net means *both drivers on at full 300 mA each*. The XIAO leaves that net
undriven more often than is obvious:

- during reset and the ~100 ms before `init_ledc()` parks the pin;
- throughout every USB flash;
- **for the entire duration of every light sleep** — with `CONFIG_PM_ENABLE=y`, ESP-IDF
  runs `esp_sleep_config_gpio_isolate()` at startup, which sets every valid GPIO to
  `GPIO_MODE_DISABLE` + `GPIO_FLOATING` while asleep, overriding the pull configured in
  `gpio_config()`. This was observed on hardware: the filaments ran at 600 mA through
  each 10 s sleep and went dark only during the keep-alive wake, which reads to the eye
  as the lamp blinking *off* periodically rather than on. The firmware now calls
  `gpio_sleep_sel_dis(DRIVER_CE_GPIO)` to opt the pad out of that switching;
- any time the firmware panics.

The resistor makes "drivers off" the resting state of the board rather than something the
firmware has to keep asserting, and it is the only one of those four cases that a code fix
cannot reach. It costs nothing at idle, since CE is already low whenever the lamp is off.
This is the same reasoning as the 100 kΩ gate pulldown on the 2N7000 one row above — the
CE net simply needs a stiffer value, because it is fighting the modules' internal pull-ups
rather than only leakage. Confirm with a meter: XIAO unpowered, CE should sit near 0 V.

---

## 10. Board layout (ElectroCookie)

Divide into a **quiet half** and a **current half**.

- **Left edge:** power entry and XIAO, oriented so its USB-C overhangs the board edge and
  stays reachable for flashing.
- **Right / lower half:** both driver modules, the four power resistors, bulk caps. Keep
  each `+5V → driver → 4.7 Ω → filament → GND` loop physically small. Filaments leave on
  flying leads.
- **Upper half, away from the drivers:** pot and radar leads. Run radar wiring several cm
  from the filament leads and do not bundle them.

The 2 W resistors run warm by design — 423 mW each in the ballasts. Give them air and do
not tuck them under the driver modules.

**Radar mounting:** 24 GHz passes through plastic and glass but not metal, so the LD2410S
can sit behind the fused glass panel. Range is 0.2–8 m over roughly ±60°; expect it to
trigger on movement outside the room's sightlines unless you narrow it over UART.

---

## 11. Bring-up

In order. Each step is cheap and catches a different failure.

1. **Verify the PD trigger outputs 5 V and stays there.** §8, steps 1–3. Do this first;
   everything downstream dies if it is wrong.
2. **Characterise the powerbank.** Find the actual shutoff threshold rather than trusting
   the 45–100 mA figure from the literature. The 10 W cement resistor kit gives a clean
   load ladder across 5 V:

   | Resistor | Load current |
   |---|---:|
   | 1 kΩ | 5.0 mA |
   | 470 Ω | 10.6 mA |
   | 300 Ω | 16.7 mA |
   | 200 Ω | 25 mA |
   | 150 Ω | 33 mA |
   | 100 Ω | 50 mA |

   Walk down the ladder, timing how long the bank stays up at each. The lowest current that
   holds it awake indefinitely is what the keep-alive pulse has to clear, and the shutdown
   delay sets `KEEPALIVE_PERIOD_US`. Also test whether the PD contract alone keeps it awake
   (§6). Dissipation is trivial for these parts — 25 mW into a 10 W body at the 1 kΩ end.
3. **Confirm the radar is genuinely an LD2410S.** Power it from 3V3 and measure supply
   current. Expect well under 1 mA. If you see tens of mA you have a B or C variant and the
   runtime figures do not apply.
4. **Bare XIAO.** `pio run -t upload`, confirm the board enumerates. D0/D8/D9 unconnected.
5. **Calibrate RISET.** One driver, 5.6 kΩ + 470 Ω, one filament with its 4.7 Ω ballast,
   5 V. **Measure actual current in series.** Swap the 470 Ω trim value from the kit's
   100/120/150/220/330/470/1k range until you land where you want, then match the second
   channel.
6. **Thermal soak.** Run one channel at 300 mA for 30 minutes. Watch for brightness
   drifting down — that is thermal foldback and means the ballast is too small. The CN5711
   should be warm, not painful.
7. **Second channel.** Common the CE pins. Confirm both filaments track; compare against a
   white card.
8. **Calibrate the ADC.** With `DEBUG_LOGGING 1` the firmware prints one line per second:

   ```
   I (12345) fused_glass: DEBUG: state=ON radar=1 filtered=1 adc=2950 duty=8191
   ```

   **`adc=` is the field you want.** Do not read `radar=` — that is OT2's 0/1 logic level,
   not the pot. And `duty=` cannot substitute for `adc=`: `adc_to_duty()` clamps its input
   at `ADC_RAW_AT_MAX`, so every reading at or above the *current* constant collapses to
   `duty=8191`, hiding exactly the overshoot being measured.

   Turn the pot fully clockwise, let `adc=` settle, and set `ADC_RAW_AT_MAX` in `main.c` to
   what you actually see — expect roughly 2950–2970 with the 4.7 kΩ top leg (**2950
   measured on this unit**). Left wrong, the lamp either never reaches full brightness or
   the top of the travel does nothing.

   The line only prints while the firmware is awake, i.e. `state=ON`. Stay inside the
   radar's coverage: step away for 25 s and it fades out, enters light sleep, and the log
   stops entirely. That is the off-delay working, not a fault.

   Three things to confirm while you are here:

   | Check | Method | Bad result means |
   |---|---|---|
   | Ceiling | Fully CW | `4095` pegged → top leg missing or shorted; wiper on 3V3 |
   | Direction | CW vs CCW | Max at CCW → pot pins 1 and 3 swapped; the firmware has no invert, so swap the wires |
   | Linearity | Slow full sweep | Increments bunched at one end → trimmer is not linear taper (§2.2) |
   | Noise | Hands off | Wander approaching `ADC_HYSTERESIS` (75) → missing 100 nF at D1, or an over-long wiper lead |

   Then reflash and confirm fully CW gives `duty=8191`, and fully CCW gives `duty=410` —
   **not** 0. `MIN_ON_DUTY` is a deliberate floor, so the pot alone never blacks the lamp
   out; only the occupancy timeout does that.
9. **Radar behaviour.** Log OT2. Walk up, then **stand perfectly still for a minute — OT2
   must stay high.** That static-presence behaviour is the entire reason for this sensor.
   Tune sensitivity over UART if it drops out.
10. **Keep-alive current.** Measure the actual pulse current (§6). Drop 33 Ω to 22 Ω if it
    lands under the threshold you found in step 2.
11. **Integration.** Full firmware. Confirm the 25 s timeout, the fade, and that the lamp
    relights instantly on approach.
12. **Idle current.** Lamp off, meter the whole assembly **with USB disconnected** — the
    USB Serial/JTAG console holds the chip awake and will read far above the design figure.

    **Watch the filaments through several sleep cycles first, by eye.** Anything above a
    few mA here, or any visible glow or periodic flash between keep-alive wakes, means the
    CE net is floating during sleep (§9) — not a measurement error. You cannot debug this
    over the serial log: light sleep powers down the USB PHY, so the console drops and the
    log simply ends at `No presence for 25 s. OFF.` That silence is correct behaviour, and
    it is why this failure is invisible in the terminal and obvious in the dark.
13. **Overnight.** Leave it 12 hours untouched, then walk up. If it does not light, the
    powerbank slept: lengthen `KEEPALIVE_PULSE_MS`.

---

## 12. Known risks

| Risk | Consequence | Mitigation |
|---|---|---|
| **PD trigger set above 5 V** | **Instant loss of both drivers, both filaments, and the XIAO** | Set 5 V, engage button lock, verify across power cycles — §8 |
| Trigger variant has USB-C socket output | Cannot wire to the board | Check on arrival; add a USB-C female breakout |
| Radar is secretly an LD2410B/C | Idle draw 175× budget, runtime collapses to hours | Measure supply current at step 3 |
| Powerbank auto-shutoff | Lamp dead until manually restarted | Keep-alive pulse; load ladder at step 2; overnight test |
| CN5711 thermal foldback | Lamp silently dims after minutes | 4.7 Ω ballast; step 6 |
| **CE net left undriven** | **Both drivers full on at 600 mA — during sleep, reset, flashing and any panic. Drains the bank and invalidates every idle measurement** | 10 kΩ pulldown on the CE net (§9); `gpio_sleep_sel_dis()` in `init_ledc()` |
| PWM above 2 kHz | Erratic regulation, not just wrong brightness | `LEDC_FREQUENCY 1000`, XTAL clock so DFS cannot shift it |
| RISET constant mismatch | Wrong drive current | Measure and swap the trim resistor, step 5 |
| `ADC_RAW_AT_MAX` unset | Dead zone at one end of the knob | Step 8 |
| Trimmer is not linear taper | Brightness bunches at one end of travel | Sweep and check at step 8; swap in a WH148 panel pot |
| 2N7000 at 3.3 V gate | Keep-alive pulse weaker than designed | Measure; drop to 22 Ω if needed |
| Strapping pins D0/D8/D9 | Board will not boot or flash | Leave unconnected |
| Boot log on GPIO21 | Corrupts radar UART | Radar UART on D4/D5 |
| 1 kHz banding on camera | Stripes when photographing the piece | Shoot at full brightness or ≥1/60 s |
| USB attached during measurement | Idle current reads ~25 mA, not ~6 mA | Measure on the powerbank alone |

---

## 13. Upgrade path

Swapping the CN5711 modules for **LD3190SB buck drivers** (3.3–32 V in, 94%, 300 mA
option, PWM dimming) cuts the on-state from 625 mA to ~383 mA — **43.5 h continuous instead
of 26.6 h** — and deletes the ballast resistors and the thermal problem entirely.

The PD trigger module makes this easier than it would otherwise be: the buck driver accepts
anything from 3.3 V to 32 V, so you can feed it whatever voltage the bank negotiates most
efficiently rather than being pinned to 5 V. Firmware would need the PWM ceiling
re-checked against that part's dimming input, since the 1 kHz limit is a CN5711 constraint,
not a universal one.

---

## Sources

- CN5711 datasheet (θJA 300 °C/W, 135 °C thermal regulation, dropout, RISET formula, CE PWM < 2 kHz) — https://electronperdido.com/wp-content/uploads/2024/04/CN5711-datasheet.pdf
- CN5711 driver module — https://www.amazon.com/dp/B0F1K97V61
- AITRIP USB-C PD trigger module — https://www.amazon.com/dp/B0D7CFSCP6
- Seeed XIAO ESP32C3 wiki (pinout, ADC1/ADC2, strapping pins, D0–D3 wake, 5 V pin behaviour) — https://wiki.seeedstudio.com/XIAO_ESP32C3_Getting_Started/
- HLK-LD2410S radar — https://www.gravityelectronic.com/shop/sensors-modules-7/radar-sensor-module-33v-low-power-hlk-ld2410s-12883
- LED filaments — https://www.amazon.com/dp/B0CV83D25S
- Chanzon 2 W metal film resistor kit (on hand) — https://www.amazon.com/dp/B08QR72BFW
- BOJACK 1/2 W metal film resistor kit, 25 values (on hand) — https://www.amazon.com/dp/B08FHPJ5G8
- BOJACK 6 mm potentiometer kit, 15 values (on hand) — https://www.amazon.com/dp/B07WHJMVR4
- JuForAcc 10 W cement resistor kit (bench use) — https://www.amazon.com/dp/B0FH4STPP7
- Powerbank auto-shutoff thresholds — https://powerbankzone.com/power-bank-keeps-switching-off/
- Anker Trickle Charging Mode, 2-hour timeout — https://service.anker.com/article-description/What-is-Trickle-Charging-Mode
- Adafruit, keeping smart power banks alive at low currents — https://blog.adafruit.com/2020/03/09/keeping-smart-power-banks-alive-while-drawing-low-currents/
- LD3190SB buck CC driver (upgrade path) — https://eletechsup.com/products/ld3190sb-multifunction-dc-dc-buck-constant-current-driver-dc-3-3-30v-200ma-300-450-700-900ma-led-dimmer-pwm-controller-module-ld3190sb
