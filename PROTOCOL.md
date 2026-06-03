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
