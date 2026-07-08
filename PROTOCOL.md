# AquaControl — USB HID Protocol Documentation

Reverse-engineered specifications for direct USB HID communication with Aquacomputer devices on Linux, bypassing the kernel drivers.

## Supported Devices
* **Aquaero 6 LT** (VID: `0x0c70`, PID: `0xf001`)
* **Farbwerk 360** (VID: `0x0c70`, PID: `0xf010`)

---

# Aquaero 6 LT

The Aquaero 6 LT section was reverse-engineered separately. The values below reflect the logic implemented in `engine.py`.

## Device
* **Vendor ID:** `0x0c70`
* **Product ID:** `0xf001`

## Channel Mode Switch (PWM / DC)
Hot-switching a fan channel between control modes means reading a configuration block, flipping one byte, and writing the whole block back as a USB Feature Report.

* **Target Report ID:** `0x0B`
* **Payload size:** 1025 bytes (`buf[0]` is always the Report ID `0x0B`)

### Memory offsets (mode byte per channel)
* **Channel 1:** index `539`
* **Channel 2:** index `559`
* **Channel 3:** index `579`
* **Channel 4:** index `599`

### Accepted values
* `0x00` — Power-controlled mode (DC / voltage regulation)
* `0x02` — PWM mode

### Execution flow
1. Open HID communication on the device path.
2. `get_feature_report` for the 1025-byte report `0x0B`.
3. Modify the byte at the target index (e.g. `buf[539] = 0x02` for PWM on channel 1).
4. Send the full 1025-byte buffer back (`send_feature_report`).

## Flow-sensor calibration (impulses per litre)
Writes a 16-bit little-endian "impulses per litre" value to EEPROM.

* **Target Report ID:** `0x0B`
* **Payload size:** 1025 bytes

### Memory offsets (16-bit, little-endian)
* **Flow sensor 1:** index `416` (bytes 416–417)
* **Flow sensor 2:** index `422` (bytes 422–423)

### Encoding
* `buf[target]     = impulses & 0xFF`        (low byte)
* `buf[target + 1] = (impulses >> 8) & 0xFF` (high byte)

### Execution flow
1. Open HID communication.
2. `get_feature_report` for the 1025-byte report `0x0B`.
3. Split the value into low/high bytes.
4. Overwrite the two bytes at the target index.
5. Send the full buffer back.

---

# Farbwerk 360

Verified against real Aquasuite traffic: the engine reproduces the header, every active slot, the routing table and the CRC byte-for-byte. Firmware observed: `1025`.

## Device
* **Vendor ID:** `0x0c70`
* **Product ID:** `0xf010`
* **Interface:** 1 (feature reports)

## Model in one paragraph
The board drives its LEDs through up to **20 "virtual controllers"** (what the UI calls *strips*). Each strip carries one static colour **or one hardware effect** and is mapped to a physical channel and a start position by a small **routing table**. Everything travels in a single **1666-byte** block sent as **Report ID `0x03`**. This document describes the *static-colour* payload and all the shared framing (header, routing, CRC, flash). The **hardware effects are decoded** in the companion file `PROTOCOL_EFFETTI.md`: they live in the very same 70-byte slot and change only its contents.

## Payload map (1666 bytes, Report ID `0x03`)

| Bytes | Meaning |
|---|---|
| `0` | Report ID `0x03` |
| `0`–`18` | Constant 19-byte header. Contains global brightness at byte `16`. |
| `19`–`1418` | **20 slots × 70 bytes** (virtual controllers). Slot `k` starts at `19 + 70·k`. |
| `1419`–`1478` | **Routing table**: up to 20 records × 3 bytes, contiguous, terminated by zeros. |
| `1479`–`1601` | Reserved / constant padding. |
| `1602`–`1663` | Constant footer/padding. |
| `1664`–`1665` | **CRC16** over bytes `1`–`1663`. |

## Slot structure — one virtual controller (70 bytes)

| Offset | Meaning |
|---|---|
| `+0` | **Enable.** `0x0F` = active. |
| `+1` | **Mode / effect id.** |
| `+5` | **FLAGS** (for effects). |
| `+9` | Constant `0x0F` (strip width = 15). |
| `+23 …` | **Parameters** (16-bit little-endian, effects only). |
| `+46 …` | **Palette** (effects only) or **Colour** (static). |
| `+47,+48,+49` | **Colour** (G, R, B order; static slots only). |

## Routing table (from byte `1419`)

Up to 20 records, **3 bytes each**:

| Byte | Meaning |
|---|---|
| `0` | **Controller** = slot index + 1 (creation order). |
| `1` | **Channel**, 0-based (RGBpx1 = `0` … RGBpx4 = `3`). |
| `2` | **Start LED**, 0-based (LED 1 → `0`). |

Records are sorted by **channel ascending, controller descending**.

## CRC16 (bytes `1664`–`1665`)

* **Width:** 16
* **Polynomial:** `0x8005`
* **Init:** `0xFFFF`
* **Reflect in/out:** yes/yes
* **Final XOR:** `0xFFFF`
* **Storage:** big-endian

## Applying vs saving

* **Apply (live preview):** send the 1666-byte payload as **Feature Report `0x03`**.
* **Save (permanent):** send Output report `02 00 00 00 02 00 00 00 00 34 C6`.

## Open questions / next reverse-engineering targets

1. **Hardware effects:** Fully decoded and implemented; full spec in `PROTOCOL_EFFETTI.md`.
2. **Variable strip width:** Clarified as fixed 15-LED strips; variable width is not supported by the protocol and not needed.
3. **Crash / fault payload:** Future target. Capture the input report sent to the host when a channel short-circuits to surface red warnings in the GUI.
