# Farbwerk 360 — Protocollo EFFETTI HARDWARE

Estensione di `PROTOCOL.md`. Documenta la struttura degli **effetti hardware** del Farbwerk 360 (rotating rainbow, breathing, scanner, rain, ...).

Un effetto **non cambia nulla** del resto del protocollo: vive dentro i 70 byte di uno *slot* (controller virtuale), esattamente come un colore statico. Header, luminosità (byte 16), tabella di routing (da 1419), CRC16 (1664‑1665) e il salvataggio in flash restano **identici** a quanto già documentato.

---

## 1. Struttura di uno slot con effetto (70 byte)

Offset **relativi all'inizio dello slot** (slot *k* = 19 + 70·*k*):

| Offset | Contenuto |
|-------:|-----------|
| `+0`   | `0x0F` — slot acceso |
| `+1`   | **MODE** — identificativo dell'effetto (vedi §2). `0x01` = colore statico |
| `+2 … +22` | **Scheletro** costante per ciascun effetto |
| `+5`   | **FLAGS** — bitfield (reverse / fade / random / slide / snow / …) |
| `+23, +25, +27, …` | **PARAMETRI**, ognuno intero **16 bit LITTLE‑ENDIAN**. Fino a 9 parole (fino a `+40`) |
| `+41 … +45` | zero (padding) |
| `+46 … +69` | **PALETTE**: 6 voci × 4 byte |

Nota: `+5` fa parte dell'area `+2…+22` ma è l'unico byte di quella zona che cambia in funzione delle opzioni; il resto dello scheletro è costante per un dato MODE.

### Parametri a 16 bit

La parola *k* (k = 0,1,2,…) sta agli offset `23+2k` (basso) e `23+2k+1` (alto):

```python
valore = slot[23+2k] | (slot[23+2k+1] << 8)
```

### Palette (offset 46‑69)

6 voci da 4 byte, formato **`[A, G, R, B]`** (colore in ordine **G‑R‑B**):

```text
voce k  ->  offset 46+4k
            +0 = A  (intensità voce, sempre 0xFF)
            +1 = G
            +2 = R
            +3 = B
```

La **voce 0** è lo **sfondo** (se previsto dall'effetto). Le voci non usate restano al valore di default della scheda (rosso pieno, A=0xFF).

---

## 2. Tabella dei MODE

| MODE | Effetto | MODE | Effetto |
|-----:|---------|-----:|---------|
| `0x01` | static (colore fisso) | `0x0B` | color sequence |
| `0x02` | breathing | `0x0C` | color shift |
| `0x03` | rotating rainbow | `0x0D` | *(non catturato)* |
| `0x04` | blinking | `0x0E` | flame |
| `0x05` | color change | `0x0F` | rain |
| `0x06` | *(non catturato)* | `0x10` | snowfall |
| `0x07` | sequence | `0x11` | stardust |
| `0x08` | scanner | `0x12` | *(non catturato)* |
| `0x09` | laser | `0x13` | swiping rainbow |
| `0x0A` | wave | | |

Mancano all'appello i MODE **`0x06`, `0x0D`, `0x12`** (effetti non presenti nelle catture di Aquasuite).

---

## 3. Parametri e palette per effetto

`k` = indice della parola a 16 bit (offset `23+2k`).

### rotating rainbow (0x03)
- **Parametri:** `speed`=k0, `color_range`=k1
- **Flags:** `reverse` = `0x02`
- **Palette:** nessun colore utente (arcobaleno interno)

### swiping rainbow (0x13)
- **Parametri:** `point_speed`=k0, `point_smoothness`=k1, `point_size`=k2, `color_change_speed`=k3, `color_range`=k4
- **Flags:** `reverse` = `0x01`
- **Palette:** voce0 = **point color**, voce1 = **strip color**

### breathing (0x02)
- **Parametri:** `speed`=k0, `intensity`=k1, `delay_max`=k2 (delay max brightness), `delay_min`=k3 (delay min brightness)
- **Palette:** voce0 = colore unico

### color shift (0x0C)
- **Parametri:** `speed`=k0, `color_range`=k1, `total_area`=k2
- **Flags:** `reverse` = `0x02`
- **Palette:** voce0 = colore unico

### color change (0x05)
- **Parametri:** `speed`=k0, `count`=k1 (numero di colori)
- **Flags:** `fade` = `0x04`, `random_color` = `0x08`, `slide_colors` = `0x10`
- **Palette:** lista colori voci 0…count‑1 (nessuno sfondo)

### blinking (0x04)
- **Parametri:** `speed`=k0, `count`=k1 (numero di colori di primo piano)
- **Flags:** `fade_in` = `0x02`, `fade_out` = `0x04`, `random_color` = `0x08`, `slide_colors` = `0x10`
- **Palette:** voce0 = **background**, voci 1… = colori

### color sequence (0x0B)
- **Parametri:** `speed`=k0, `smoothness`=k1, *(k2 = 1, non interpretato)*, `count`=k3, `color_change_speed`=k4
- **Flags:** `reverse` = `0x02`, `random_color` = `0x08`
- **Palette:** lista colori (nessuno sfondo)

### sequence (0x07)
- **Parametri:** `speed`=k0, `smoothness`=k1, `count`=k2, `delay_after`=k3 (delay after sequence), `delay_before`=k4 (delay before sequence)
- **Flags:** `reverse` = `0x02`, `fade` = `0x04`, `random_color` = `0x08`
- **Palette:** voce0 = **background**, voci 1… = colori

### scanner (0x08)
- **Parametri:** `speed`=k0, `smoothness`=k1, `width`=k2, `start_delay`=k3, `interval_min`=k4, `interval_max`=k5
- **Flags:** `reverse` = `0x02`, `random_color` = `0x08`, `color_mode2` = `0x20`, `color_change` = `0x40`, `circular` = `0x80`
- **Palette:** voce0 = background, voce1 = color1, voce2 = color2

### laser (0x09)
- **Parametri:** come **scanner** (k0…k5)
- **Flags:** `reverse` = `0x02`, `random_color` = `0x08`, `color_mode2` = `0x20`, `color_change` = `0x40`, `circular` = `0x80`
- **Palette:** voce0 = background, voce1 = color1, voce2 = color2

### wave (0x0A)
- **Parametri:** `speed`=k0, `smoothness`=k1, `width`=k2, `start_delay`=k5, `interval_max` (= *Delay max*) =k7.
- **Flags:** `reverse` = `0x02`, `random_color` = `0x08`, `circular` = `0x80`
- **Palette:** voce0 = background, voci 1… = colori

### flame (0x0E)
- **Parametri:** `intensity`=k0
- **Palette:** voce0 = background, voce1 = color1, voce2 = color2

### rain (0x0F)
- **Parametri:** `drop_speed`=k0, `drop_items`=k1, `drop_size`=k2, `drop_smoothness`=k3, `runtime`=k4, `interval_min` (*Delay min*) =k5, `interval_max` (*Delay max*) =k6
- **Flags:** `snow` = `0x10`, `reverse` = `0x02`, `random_color` = `0x08`
- **Palette:** voce0 = background, voce1 = color

### snowfall (0x10) / stardust (0x11)
- **Parametri:** layout **identico a Rain**. `drop_speed`=k0, `drop_items`=k1, `drop_size`=k2, `drop_smoothness`=k3, `runtime`=k4, `interval_min` (*Delay min*) =k5, `interval_max` (*Delay max*) =k6
- **Flags:** `reverse` = `0x02`, `random_color` = `0x08`, `snow` = `0x10`
- **Palette:** voce0 = background, voce1 = color

---

## 4. Riepilogo encoding (pseudocodice)

```python
slot = scheletro_del_MODE[0..69]          # 70 byte, costante per l'effetto
slot[0]  = 0x0F
slot[1]  = MODE
slot[5]  = OR dei bitmask dei flag attivi

for k, valore in enumerate(parametri):    # ordine specifico dell'effetto
    slot[23+2k]   =  valore & 0xFF
    slot[23+2k+1] = (valore >> 8) & 0xFF
    
for k, (R,G,B) in enumerate(palette):     # voce0 = sfondo (se previsto)
    slot[46+4k+0] = 0xFF                   # A
    slot[46+4k+1] = G
    slot[46+4k+2] = R
    slot[46+4k+3] = B
    
# le voci di palette non usate restano al default della scheda
```
