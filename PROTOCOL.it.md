# Aquaero 6 LT - USB HID Protocol Documentation

Questo documento descrive le specifiche tecniche e gli offset di memoria ricavati tramite reverse engineering per la comunicazione diretta via USB HID con la scheda Aquaero 6 LT, bypassando i driver del kernel Linux.

## Specifiche del Dispositivo
* **Vendor ID:** `0x0c70`
* **Product ID:** `0xf001` (Aquaero 6)

## Switch Modalità Canale (PWM / DC)
Il cambio di modalità a caldo delle ventole richiede la lettura e sovrascrittura di uno specifico blocco di memoria di configurazione tramite l'invio di un Feature Report USB.

* **Report ID Target:** `0x0B`
* **Dimensione Payload:** 1025 bytes (Il primo byte `buf[0]` contiene sempre il Report ID `0x0B`)

### Offset di Memoria
I byte responsabili per la modalità di alimentazione dei singoli canali si trovano ai seguenti offset esatti all'interno del payload da 1025 bytes:
* **Canale 1:** Indice `539`
* **Canale 2:** Indice `559`
* **Canale 3:** Indice `579`
* **Canale 4:** Indice `599`

### Valori Accettati (Payload Hex)
Per modificare la modalità del canale, è necessario sovrascrivere il byte all'indice corrispondente con uno dei seguenti valori:
* `0x00` : Modalità Power Controlled (DC / Regolazione di Voltaggio)
* `0x02` : Modalità PWM

**Flusso di esecuzione:**
1. Aprire la comunicazione HID sul path del dispositivo.
2. Richiedere il Feature Report `0x0B` di 1025 bytes (`get_feature_report`).
3. Modificare il byte all'indice target (es. `buf[539] = 0x02` per PWM su Canale 1).
4. Rispedire l'intero buffer di 1025 bytes al dispositivo (`send_feature_report`).
