# Farbwerk 360 — HARDWARE EFFECTS Protocol

Extension of `PROTOCOL.md`. Documents the structure of the Farbwerk 360's **hardware effects** (rotating rainbow, breathing, scanner, rain, ...).

An effect **changes nothing** in the rest of the protocol: it lives inside the 70 bytes of a *slot* (virtual controller), exactly like a static colour. Header, brightness (byte 16), routing table (from 1419), CRC16 (1664-1665) and the flash save remain **identical** to what is already documented.

---

## 1. Structure of a slot with an effect (70 bytes)

Offsets **relative to the start of the slot** (slot *k* = 19 + 70·*k*):

| Offset | Content |
|-------:|---------|
| `+0`   | `0x0F` — slot on |
| `+1`   | **MODE** — effect identifier (see §2). `0x01` = static colour |
| `+2 … +22` | **Skeleton** constant for each effect |
| `+5`   | **FLAGS** — bitfield (reverse / fade / random / slide / snow / …) |
| `+23, +25, +27, …` | **PARAMETERS**, each a **16-bit LITTLE-ENDIAN** integer. Up to 9 words (up to `+40`) |
| `+41 … +45` | zero (padding) |
| `+46 … +69` | **PALETTE**: 6 entries × 4 bytes |

Note: `+5` is part of the `+2…+22` area but is the only byte of that zone that changes with the options; the rest of the skeleton is constant for a given MODE.

### 16-bit parameters

Word *k* (k = 0,1,2,…) is at offsets `23+2k` (low) and `23+2k+1` (high):

```python
value = slot[23+2k] | (slot[23+2k+1] << 8)
```

### Palette (offsets 46-69)

6 entries of 4 bytes, format **`[A, G, R, B]`** (colour in **G-R-B** order):

```text
entry k  ->  offset 46+4k
             +0 = A  (entry intensity, always 0xFF)
             +1 = G
             +2 = R
             +3 = B
```

**Entry 0** is the **background** (if provided by the effect). Unused entries stay at the board's default value (full red, A=0xFF).

---

## 2. MODE table

| MODE | Effect | MODE | Effect |
|-----:|--------|-----:|--------|
| `0x01` | static (fixed colour) | `0x0B` | color sequence |
| `0x02` | breathing | `0x0C` | color shift |
| `0x03` | rotating rainbow | `0x0D` | *(not captured)* |
| `0x04` | blinking | `0x0E` | flame |
| `0x05` | color change | `0x0F` | rain |
| `0x06` | *(not captured)* | `0x10` | snowfall |
| `0x07` | sequence | `0x11` | stardust |
| `0x08` | scanner | `0x12` | *(not captured)* |
| `0x09` | laser | `0x13` | swiping rainbow |
| `0x0A` | wave | | |

The MODEs **`0x06`, `0x0D`, `0x12`** are missing (effects not present in the Aquasuite captures).

---

## 3. Parameters and palette per effect

`k` = index of the 16-bit word (offset `23+2k`).

### rotating rainbow (0x03)
- **Parameters:** `speed`=k0, `color_range`=k1
- **Flags:** `reverse` = `0x02`
- **Palette:** no user colour (internal rainbow)

### swiping rainbow (0x13)
- **Parameters:** `point_speed`=k0, `point_smoothness`=k1, `point_size`=k2, `color_change_speed`=k3, `color_range`=k4
- **Flags:** `reverse` = `0x01`
- **Palette:** entry0 = **point color**, entry1 = **strip color**

### breathing (0x02)
- **Parameters:** `speed`=k0, `intensity`=k1, `delay_max`=k2 (delay max brightness), `delay_min`=k3 (delay min brightness)
- **Palette:** entry0 = single colour

### color shift (0x0C)
- **Parameters:** `speed`=k0, `color_range`=k1, `total_area`=k2
- **Flags:** `reverse` = `0x02`
- **Palette:** entry0 = single colour

### color change (0x05)
- **Parameters:** `speed`=k0, `count`=k1 (number of colours)
- **Flags:** `fade` = `0x04`, `random_color` = `0x08`, `slide_colors` = `0x10`
- **Palette:** colour list, entries 0…count-1 (no background)

### blinking (0x04)
- **Parameters:** `speed`=k0, `count`=k1 (number of foreground colours)
- **Flags:** `fade_in` = `0x02`, `fade_out` = `0x04`, `random_color` = `0x08`, `slide_colors` = `0x10`
- **Palette:** entry0 = **background**, entries 1… = colours

### color sequence (0x0B)
- **Parameters:** `speed`=k0, `smoothness`=k1, *(k2 = 1, not interpreted)*, `count`=k3, `color_change_speed`=k4
- **Flags:** `reverse` = `0x02`, `random_color` = `0x08`
- **Palette:** colour list (no background)

### sequence (0x07)
- **Parameters:** `speed`=k0, `smoothness`=k1, `count`=k2, `delay_after`=k3 (delay after sequence), `delay_before`=k4 (delay before sequence)
- **Flags:** `reverse` = `0x02`, `fade` = `0x04`, `random_color` = `0x08`
- **Palette:** entry0 = **background**, entries 1… = colours

### scanner (0x08)
- **Parameters:** `speed`=k0, `smoothness`=k1, `width`=k2, `start_delay`=k3, `interval_min`=k4, `interval_max`=k5
- **Flags:** `reverse` = `0x02`, `random_color` = `0x08`, `color_mode2` = `0x20`, `color_change` = `0x40`, `circular` = `0x80`
- **Palette:** entry0 = background, entry1 = color1, entry2 = color2

### laser (0x09)
- **Parameters:** like **scanner** (k0…k5)
- **Flags:** `reverse` = `0x02`, `random_color` = `0x08`, `color_mode2` = `0x20`, `color_change` = `0x40`, `circular` = `0x80`
- **Palette:** entry0 = background, entry1 = color1, entry2 = color2

### wave (0x0A)
- **Parameters:** `speed`=k0, `smoothness`=k1, `width`=k2, `start_delay`=k5, `interval_max` (= *Delay max*) =k7.
- **Flags:** `reverse` = `0x02`, `random_color` = `0x08`, `circular` = `0x80`
- **Palette:** entry0 = background, entries 1… = colours

### flame (0x0E)
- **Parameters:** `intensity`=k0
- **Palette:** entry0 = background, entry1 = color1, entry2 = color2

### rain (0x0F)
- **Parameters:** `drop_speed`=k0, `drop_items`=k1, `drop_size`=k2, `drop_smoothness`=k3, `runtime`=k4, `interval_min` (*Delay min*) =k5, `interval_max` (*Delay max*) =k6
- **Flags:** `snow` = `0x10`, `reverse` = `0x02`, `random_color` = `0x08`
- **Palette:** entry0 = background, entry1 = color

### snowfall (0x10) / stardust (0x11)
- **Parameters:** layout **identical to Rain**. `drop_speed`=k0, `drop_items`=k1, `drop_size`=k2, `drop_smoothness`=k3, `runtime`=k4, `interval_min` (*Delay min*) =k5, `interval_max` (*Delay max*) =k6
- **Flags:** `reverse` = `0x02`, `random_color` = `0x08`, `snow` = `0x10`
- **Palette:** entry0 = background, entry1 = color

---

## 4. Encoding summary (pseudocode)

```python
slot = skeleton_of_MODE[0..69]            # 70 bytes, constant for the effect
slot[0]  = 0x0F
slot[1]  = MODE
slot[5]  = OR of the bitmasks of the active flags

for k, value in enumerate(parameters):    # effect-specific order
    slot[23+2k]   =  value & 0xFF
    slot[23+2k+1] = (value >> 8) & 0xFF
    
for k, (R,G,B) in enumerate(palette):     # entry0 = background (if provided)
    slot[46+4k+0] = 0xFF                   # A
    slot[46+4k+1] = G
    slot[46+4k+2] = R
    slot[46+4k+3] = B
    
# unused palette entries stay at the board default
```
