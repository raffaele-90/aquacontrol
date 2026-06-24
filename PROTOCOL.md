# Aquaero 6 LT - USB HID Protocol Documentation

This document outlines the technical specifications and memory offsets obtained via reverse engineering for direct USB HID communication with the Aquaero 6 LT, bypassing Linux kernel drivers.

## Device Specifications
* **Vendor ID:** `0x0c70`
* **Product ID:** `0xf001` (Aquaero 6)

## Channel Mode Switch (PWM / DC)
Hot-switching the fan control modes requires reading and overwriting a specific configuration memory block by sending a USB Feature Report.

* **Target Report ID:** `0x0B`
* **Payload Size:** 1025 bytes (The first byte `buf[0]` always contains the Report ID `0x0B`)

### Memory Offsets
The bytes responsible for the power delivery mode of the individual channels are located at the following exact offsets within the 1025-byte payload:
* **Channel 1:** Index `539`
* **Channel 2:** Index `559`
* **Channel 3:** Index `579`
* **Channel 4:** Index `599`

### Accepted Values (Hex Payload)
To change the channel mode, overwrite the byte at the corresponding index with one of the following values:
* `0x00` : Power Controlled Mode (DC / Voltage Regulation)
* `0x02` : PWM Mode

**Execution Flow:**
1. Open HID communication on the device path.
2. Request the 1025-byte Feature Report `0x0B` (`get_feature_report`).
3. Modify the byte at the target index (e.g., `buf[539] = 0x02` for PWM on Channel 1).
4. Send the entire 1025-byte buffer back to the device (`send_feature_report`).

## Flow Sensor Calibration (Impulses per Liter)
Calibrating the flow sensors requires writing a 16-bit integer (Little Endian) representing the "impulses per liter" value to the EEPROM.

* **Target Report ID:** `0x0B`
* **Payload Size:** 1025 bytes

### Memory Offsets
The 16-bit calibration values for the flow sensors start at the following offsets:
* **Flow Sensor 1:** Index `416` (uses 416 and 417)
* **Flow Sensor 2:** Index `422` (uses 422 and 423)

### Accepted Values (Hex Payload)
The value is an unsigned 16-bit integer (0 - 65535). It must be split into two bytes (Little Endian):
* `buf[target_index] = impulses & 0xFF` (Low byte)
* `buf[target_index + 1] = (impulses >> 8) & 0xFF` (High byte)

**Execution Flow:**
1. Open HID communication on the device path.
2. Request the 1025-byte Feature Report `0x0B`.
3. Calculate the low and high bytes of the desired calibration value.
4. Overwrite the two bytes starting at the target index.
5. Send the entire 1025-byte buffer back to the device.
