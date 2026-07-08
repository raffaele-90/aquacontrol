# AquaControl — Documentazione Protocollo USB HID

Specifiche basate su reverse-engineering per la comunicazione USB HID diretta con i dispositivi Aquacomputer su Linux, bypassando i driver del kernel.

## Dispositivi Supportati
* **Aquaero 6 LT** (VID: `0x0c70`, PID: `0xf001`)
* **Farbwerk 360** (VID: `0x0c70`, PID: `0xf010`)

---

# Aquaero 6 LT

La sezione Aquaero 6 LT è stata sottoposta a reverse-engineering separatamente. I valori sottostanti riflettono la logica implementata in `engine.py`.

## Dispositivo
* **Vendor ID:** `0x0c70`
* **Product ID:** `0xf001`

## Cambio Modalità Canale (PWM / DC)
Lo switch a caldo di un canale ventola tra le modalità di controllo implica la lettura di un blocco di configurazione, il cambio di un singolo byte e la riscrittura dell'intero blocco come USB Feature Report.

* **Target Report ID:** `0x0B`
* **Dimensione Payload:** 1025 byte (`buf[0]` è sempre il Report ID `0x0B`)

### Offset di Memoria (byte della modalità per canale)
* **Canale 1:** indice `539`
* **Canale 2:** indice `559`
* **Canale 3:** indice `579`
* **Canale 4:** indice `599`

### Valori Accettati
* `0x00` — Modalità controllata in potenza (DC / regolazione di tensione)
* `0x02` — Modalità PWM

### Flusso di Esecuzione
1. Aprire la comunicazione HID sul percorso del dispositivo.
2. Eseguire `get_feature_report` per il report `0x0B` da 1025 byte.
3. Modificare il byte all'indice di destinazione (es. `buf[539] = 0x02` per PWM sul canale 1).
4. Inviare indietro l'intero buffer di 1025 byte (`send_feature_report`).

## Calibrazione sensore di flusso (impulsi per litro)
Scrive un valore a 16-bit little-endian "impulsi per litro" nella EEPROM.

* **Target Report ID:** `0x0B`
* **Dimensione Payload:** 1025 byte

### Offset di Memoria (16-bit, little-endian)
* **Sensore di flusso 1:** indice `416` (byte 416–417)
* **Sensore di flusso 2:** indice `422` (byte 422–423)

### Codifica
* `buf[target]     = impulses & 0xFF`        (byte basso)
* `buf[target + 1] = (impulses >> 8) & 0xFF` (byte alto)

### Flusso di Esecuzione
1. Aprire la comunicazione HID.
2. Eseguire `get_feature_report` per il report `0x0B` da 1025 byte.
3. Dividere il valore in byte alto/basso.
4. Sovrascrivere i due byte all'indice di destinazione.
5. Inviare indietro l'intero buffer.

---

# Farbwerk 360

Verificato rispetto al traffico reale di Aquasuite: il motore riproduce l'intestazione, ogni slot attivo, la tabella di routing e il CRC byte per byte. Firmware osservato: `1025`.

## Dispositivo
* **Vendor ID:** `0x0c70`
* **Product ID:** `0xf010`
* **Interfaccia:** 1 (feature report)

## Il modello in un paragrafo
La scheda pilota i suoi LED attraverso un massimo di **20 "controller virtuali"** (che l'interfaccia utente chiama *strisce*). Ogni striscia trasporta un colore statico **oppure un effetto hardware** ed è mappata a un canale fisico e a una posizione di partenza tramite una piccola **tabella di routing**. Tutto viaggia in un singolo blocco da **1666 byte** inviato come **Report ID `0x03`**. Questo documento descrive il payload dei *colori statici* e tutta l'intelaiatura condivisa (intestazione, routing, CRC, flash). Gli **effetti hardware sono decodificati** nel file compagno `PROTOCOL_EFFETTI.md`: vivono negli stessi 70 byte dello slot e ne cambiano solo il contenuto.

## Mappa del Payload (1666 byte, Report ID `0x03`)

| Byte | Significato |
|---|---|
| `0` | Report ID `0x03` |
| `0`–`18` | Intestazione costante da 19-byte. Contiene la luminosità globale al byte `16`. |
| `19`–`1418` | **20 slot × 70 byte** (controller virtuali). Lo slot `k` inizia a `19 + 70·k`. |
| `1419`–`1478` | **Tabella di routing**: fino a 20 record × 3 byte, contigui, terminati da zeri. |
| `1479`–`1601` | Riservato / padding costante. |
| `1602`–`1663` | Piè di pagina/padding costante. |
| `1664`–`1665` | **CRC16** sui byte `1`–`1663`. |

## Struttura dello slot — un controller virtuale (70 byte)

| Offset | Significato |
|---|---|
| `+0` | **Abilitazione.** `0x0F` = attivo. |
| `+1` | **Modalità / id effetto.** |
| `+5` | **FLAGS** (solo per gli effetti). |
| `+9` | Costante `0x0F` (larghezza striscia = 15). |
| `+23 …` | **Parametri** (16-bit little-endian, solo effetti). |
| `+46 …` | **Palette** (solo effetti) o **Colore** (statico). |
| `+47,+48,+49` | **Colore** (ordine G, R, B; solo slot statici). |

## Tabella di routing (dal byte `1419`)

Fino a 20 record, **3 byte ciascuno**:

| Byte | Significato |
|---|---|
| `0` | **Controller** = indice dello slot + 1 (ordine di creazione). |
| `1` | **Canale**, base-0 (RGBpx1 = `0` … RGBpx4 = `3`). |
| `2` | **LED Iniziale**, base-0 (LED 1 → `0`). |

I record sono ordinati per **canale ascendente, controller discendente**.

## CRC16 (byte `1664`–`1665`)

* **Larghezza:** 16
* **Polinomio:** `0x8005`
* **Inizializzazione:** `0xFFFF`
* **Riflesso in / out:** sì / sì
* **XOR Finale:** `0xFFFF`
* **Archiviazione:** big-endian

## Applicazione vs Salvataggio

* **Applica (anteprima dal vivo):** invia il payload di 1666 byte come **Feature Report `0x03`**.
* **Salva (permanente):** invia l'Output report `02 00 00 00 02 00 00 00 00 34 C6`.

## Domande aperte / prossimi obiettivi del reverse-engineering

1. **Effetti hardware:** Completamente decodificati e implementati; specifica completa in `PROTOCOL_EFFETTI.md`.
2. **Larghezza striscia variabile:** Chiarita come strisce fisse a 15 LED; la larghezza variabile non è supportata dal protocollo e non è necessaria.
3. **Payload di crash / fault:** Obiettivo futuro. Catturare l'input report inviato all'host quando un canale va in corto circuito per mostrare avvisi rossi di emergenza nella GUI.
