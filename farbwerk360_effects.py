# AquaControl
# Copyright (C) 2026 Raffaele Schiavone
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import struct
from farbwerk360_engine import Farbwerk360Engine


# Palette "di default" della scheda (pattern dell'area spenta): ogni voce = rosso
# pieno con A=0xFF. Le voci NON usate da un effetto restano cosi', identiche a
# quello che lascia Aquasuite (il renderer le ignora comunque).
_PAL_DEFAULT_ENTRY = (0xFF, 0x00, 0xFF, 0x00)   # A, G, R, B  (=> rosso 255,0,0)

# Colore di sfondo predefinito di Aquasuite (grigio scuro) quando l'utente non
# tocca il selettore "Background". Le catture "0a0a0a" erano semplicemente questo.
_BG_DEFAULT = (10, 10, 10)   # R, G, B


class Effect:
    """Descrittore di un tipo di effetto: mode, scheletro, mappa parametri,
    semantica della palette e bit dei flag. I valori 'default_words' provengono
    da una cattura reale e riempiono i parametri non specificati (utile per gli
    effetti con parametri ancora non del tutto interpretati)."""

    def __init__(self, name, mode, skeleton_hex, words, colors,
                 flags=None, default_words=(0,)*9):
        self.name = name
        self.mode = mode
        sk = bytes.fromhex(skeleton_hex)
        if len(sk) < 70:                # da +22/+23 in poi lo slot e' tutto zero
            sk = sk + bytes(70 - len(sk))
        self.skeleton = sk               # 70 byte
        self.words = words            # dict kwarg -> k (offset 23+2k)
        self.colors = colors          # tupla che descrive l'uso della palette
        self.flags = flags or {}      # dict kwarg(bool) -> bitmask
        self.default_words = list(default_words)
        assert len(self.skeleton) == 70


# ---------------------------------------------------------------------------
# REGISTRO EFFETTI  (mode -> semantica). I nomi dei parametri corrispondono alle
# etichette di Aquasuite. Le voci 'colors':
#   ('static',)                  -> 1 colore = il colore della striscia (voce 0)
#   ('single',)                  -> 1 colore effetto (voce 0)
#   ('point_strip',)             -> voce0 = point color, voce1 = strip color
#   ('roles', [..])              -> ruoli fissi per le prime N voci
#   ('list', count_kw, has_bg)   -> lista colori variabile; se has_bg la voce0 e'
#                                   lo sfondo e i colori partono dalla voce1; il
#                                   numero di colori viene scritto nel parametro
#                                   'count_kw'.
#   ('rainbow',)                 -> nessun colore utente (arcobaleno interno)
# ---------------------------------------------------------------------------
EFFECTS = {}
def _reg(*a, **k):
    e = Effect(*a, **k); EFFECTS[e.name] = e; EFFECTS[e.mode] = e; return e

_reg('static', 0x01,
     '0f01f0000000ffff0a0f0000006400ff0000006400ff00'+'00'*24,
     words={}, colors=('static',), default_words=(0,)*9)

_reg('breathing', 0x02,
     '0f02f0000000ffff0a0f000000640164000000640164'+'00'*24,
     words={'speed':0, 'intensity':1, 'delay_max':2, 'delay_min':3},
     colors=('single',), default_words=(60,80,5,20,0,0,0,0,0))

_reg('rotating_rainbow', 0x03,
     '0f03f0000000ffff0a0f0000006401640000006400ff00'+'00'*24,
     words={'speed':0, 'color_range':1},
     colors=('rainbow',), flags={'reverse':0x02},
     default_words=(50,100,0,0,0,0,0,0,0))

_reg('blinking', 0x04,
     '0f04f0000000ffff0a0f0000006401640000006400ff00'+'00'*24,
     words={'speed':0, 'count':1},
     colors=('list','count',True),
     flags={'fade_in':0x02, 'fade_out':0x04, 'random_color':0x08, 'slide_colors':0x10},
     default_words=(40,1,0,0,0,0,0,0,0))

_reg('color_change', 0x05,
     '0f05f0000000ffff0a0f0000006401640000006400ff00'+'00'*24,
     words={'speed':0, 'count':1},
     colors=('list','count',False),
     flags={'fade':0x04, 'random_color':0x08, 'slide_colors':0x10},
     default_words=(40,2,0,0,0,0,0,0,0))

_reg('sequence', 0x07,
     '0f07f0000000ffff0a0f0000006401640000006400ff00'+'00'*24,
     words={'speed':0, 'smoothness':1, 'count':2, 'delay_after':3, 'delay_before':4},
     colors=('list','count',True),
     flags={'fade':0x04, 'reverse':0x02, 'random_color':0x08},   # confermati da cattura
     default_words=(25,30,5,10,5,0,0,0,0))

_reg('scanner', 0x08,
     '0f08f0000000ffff0a0f0000006400640000006400ff00'+'00'*24,
     words={'speed':0, 'smoothness':1, 'width':2,
            'start_delay':3, 'interval_min':4, 'interval_max':5},
     colors=('roles', ['background','color1','color2']),
     # tutti confermati da cattura
     flags={'reverse':0x02, 'random_color':0x08, 'color_mode2':0x20,
            'color_change':0x40, 'circular':0x80},
     default_words=(25,40,20,0,0,0,0,0,0))

_reg('laser', 0x09,
     '0f09f0000000ffff0a0f0000006400640000006400ff00'+'00'*24,
     words={'speed':0, 'smoothness':1, 'width':2,
            'start_delay':3, 'interval_min':4, 'interval_max':5},
     colors=('roles', ['background','color1','color2']),
     # confermati da cattura (§4-B): color_change=0x40, color_mode2=0x20.
     # Spec del Laser ora IDENTICA a Scanner.
     flags={'reverse':0x02, 'random_color':0x08, 'color_mode2':0x20,
            'color_change':0x40, 'circular':0x80},
     default_words=(25,40,20,10,10,40,0,0,0))

_reg('wave', 0x0a,
     '0f0af0000000ffff0a0f0000006400640000006400ff00'+'00'*24,
     # Mappati da sweep (§4-A): speed=k0, smoothness=k1, width=k2,
     # start_delay=k5, interval_max (= "Delay max") = k7.
     # In Aquasuite il cursore "Delay min" scrive la STESSA parola k5 di
     # "Start delay" (stesso registro) -> nessun delay_min separato.
     # k3(=1)/k4(=80)/k6 restano costanti del base (nessun cursore li muove).
     words={'speed':0, 'smoothness':1, 'width':2, 'start_delay':5, 'interval_max':7},
     colors=('list', None, True),   # sfondo + fino a 5 colori (nessun parametro count dedicato)
     # flag ancora inferiti dalla famiglia scanner (lo sweep non li ha testati)
     flags={'reverse':0x02, 'random_color':0x08, 'circular':0x80},
     default_words=(25,40,20,1,80,0,0,0,0))

_reg('color_sequence', 0x0b,
     '0f0bf0000000ffff0a0f0000006400640000006400ff00'+'00'*24,
     # k2 (=1) non interpretato; count in k3; color_change_speed in k4
     words={'speed':0, 'smoothness':1, 'count':3, 'color_change_speed':4},
     colors=('list','count',False),
     # inferiti da sequence (le catture "Color Sequence" erano in realta' Sequence/0x07)
     flags={'reverse':0x02, 'random_color':0x08},
     default_words=(30,40,1,6,80,0,0,0,0))

_reg('color_shift', 0x0c,
     '0f0cf0000000ffff0a0f0000006401640000006400ff00'+'00'*24,
     words={'speed':0, 'color_range':1, 'total_area':2},
     colors=('single',), flags={'reverse':0x02},
     default_words=(30,50,25,0,0,0,0,0,0))

_reg('flame', 0x0e,
     '0f0ef0000000ffff0a0f0000006401640000006400ff00'+'00'*24,
     words={'intensity':0},
     colors=('roles', ['background','color1','color2']),
     default_words=(50,0,0,0,0,0,0,0,0))

_reg('rain', 0x0f,
     '0f0ff0000000ffff0a0f0000006401640000006400ff00'+'00'*24,
     # confermato da cattura: runtime=k4, Delay range min=k5 / max=k6 (come snowfall/stardust)
     words={'drop_speed':0, 'drop_items':1, 'drop_size':2, 'drop_smoothness':3,
            'runtime':4, 'interval_min':5, 'interval_max':6},
     colors=('roles', ['background','color']),
     flags={'snow':0x10, 'reverse':0x02, 'random_color':0x08},   # confermati da cattura
     default_words=(40,4,25,30,0,0,0,0,0))   # runtime/delay default = 0 (continuo)

_reg('snowfall', 0x10,
     '0f10f0000000ffff0a0f0000006401640000006400ff00'+'00'*24,
     # confermati da cattura (§4-C): layout come Rain + Delay range (k5/k6).
     words={'drop_speed':0, 'drop_items':1, 'drop_size':2, 'drop_smoothness':3,
            'runtime':4, 'interval_min':5, 'interval_max':6},
     colors=('roles', ['background','color']),
     flags={'reverse':0x02, 'random_color':0x08, 'snow':0x10},   # confermati da cattura
     default_words=(50,3,10,15,0,0,0,0,0))

_reg('stardust', 0x11,
     '0f11f0000000ffff0a0f0000006401640000006400ff00'+'00'*24,
     # confermati da cattura (§4-C): layout come Rain + Delay range (k5/k6).
     words={'drop_speed':0, 'drop_items':1, 'drop_size':2, 'drop_smoothness':3,
            'runtime':4, 'interval_min':5, 'interval_max':6},
     colors=('roles', ['background','color']),
     flags={'reverse':0x02, 'random_color':0x08, 'snow':0x10},   # confermati da cattura
     default_words=(25,3,60,15,0,0,0,0,0))

_reg('swiping_rainbow', 0x13,
     '0f13f0000000ffff0a0f0000006401640000006400ff00'+'00'*24,
     words={'point_speed':0, 'point_smoothness':1, 'point_size':2,
            'color_change_speed':3, 'color_range':4},
     colors=('point_strip',), flags={'reverse':0x01},
     default_words=(35,10,5,90,25,0,0,0,0))


def _clamp8(v):  return max(0, min(255, int(round(v))))
def _clamp16(v): return max(0, min(0xFFFF, int(round(v))))


class Farbwerk360EffectsEngine(Farbwerk360Engine):
    """Motore Farbwerk 360 con supporto agli effetti hardware.

    Uso tipico:
        eng = Farbwerk360EffectsEngine()
        eng.set_brightness_percent(60)
        eng.add_effect(channel=1, start=1, effect='rotating_rainbow',
                       speed=50, color_range=100)
        eng.add_effect(channel=2, start=1, effect='scanner',
                       background=(255,255,255), colors=[(255,0,0),(0,255,0)],
                       speed=25, smoothness=40, width=20)
        eng.commit()          # anteprima live
        eng.save_to_flash()   # opzionale, permanente

    Le strisce a colore statico (add_strip / set_channel) continuano a funzionare
    identiche a prima: si possono mischiare liberamente strisce statiche ed effetti.
    """

    PAL_BASE = 46

    # ---- costruzione di uno slot-effetto (70 byte) ----
    @classmethod
    def build_effect_slot(cls, effect, flags, words, entries):
        """Costruzione a basso livello (garantita byte-esatta).
          effect  : nome o mode
          flags   : byte flags (int)
          words   : lista/tupla fino a 9 interi -> parole 16-bit LE da +23
          entries : lista di (r,g,b) o (r,g,b,a) per le voci di palette 0..5;
                    None = lascia il default della scheda per quella voce."""
        spec = EFFECTS[effect]
        s = bytearray(spec.skeleton)
        s[0] = 0x0F
        s[1] = spec.mode
        s[5] = flags & 0xFF
        for k in range(9):
            w = _clamp16(words[k]) if k < len(words) and words[k] is not None else 0
            s[23 + 2*k]     = w & 0xFF
            s[23 + 2*k + 1] = (w >> 8) & 0xFF
        # palette: prima riempi col default della scheda, poi sovrascrivi le voci date
        for k in range(6):
            A, G, R, B = _PAL_DEFAULT_ENTRY
            o = cls.PAL_BASE + 4*k
            s[o], s[o+1], s[o+2], s[o+3] = A, G, R, B
        for k, ent in enumerate(entries[:6]):
            if ent is None:
                continue
            if len(ent) == 4:
                r, g, b, a = ent
            else:
                r, g, b = ent; a = 0xFF
            o = cls.PAL_BASE + 4*k
            s[o]   = _clamp8(a)
            s[o+1] = _clamp8(g)
            s[o+2] = _clamp8(r)
            s[o+3] = _clamp8(b)
        return bytes(s)

    # ---- API amichevole: aggiungi una striscia che esegue un effetto ----
    def add_effect(self, channel, start, effect, colors=None, background=None,
                   color=None, point_color=None, strip_color=None, **params):
        """Crea un controller virtuale (striscia) che esegue un effetto.
          channel     : canale fisico 1..4 (RGBpx1..4)
          start       : LED iniziale 1..90
          effect      : nome effetto (vedi EFFECTS) o mode
          colori: a seconda dell'effetto usa 'color', 'colors', 'background',
                  'point_color'/'strip_color' (vedi sotto).
          params      : parametri nominali dell'effetto (speed, width, ...);
                        i flag booleani (reverse=True, snow=True, ...) vanno qui.
        Ritorna l'indice della striscia creata."""
        if channel not in (1, 2, 3, 4):
            raise ValueError("Canale non valido (1..4).")
        if effect not in EFFECTS:
            raise ValueError("Effetto sconosciuto: {}".format(effect))
        spec = EFFECTS[effect]

        # ---- parole/parametri ----
        words = list(spec.default_words)
        flag_byte = 0
        for key, val in params.items():
            if key in spec.words:
                words[spec.words[key]] = _clamp16(val)
            elif key in spec.flags:
                if val:
                    flag_byte |= spec.flags[key]
            else:
                raise ValueError("Parametro '{}' non valido per l'effetto '{}'. "
                                 "Ammessi: {} + flag {}".format(
                                     key, spec.name,
                                     sorted(spec.words), sorted(spec.flags)))

        # ---- palette ----
        entries = [None]*6
        kind = spec.colors[0]
        if kind in ('static', 'single'):
            c = color if color is not None else (colors[0] if colors else (255, 0, 0))
            entries[0] = tuple(c)
        elif kind == 'point_strip':
            entries[0] = tuple(point_color) if point_color else (255, 0, 0)
            entries[1] = tuple(strip_color) if strip_color else (0, 255, 0)
        elif kind == 'roles':
            roles = spec.colors[1]
            given = {}
            # sfondo di default = grigio (10,10,10), come Aquasuite quando non lo si cambia
            if 'background' in roles:
                given['background'] = background if background is not None else _BG_DEFAULT
            if color is not None:      given['color'] = color
            clist = list(colors) if colors else []
            ci = 0
            for i, role in enumerate(roles):
                if role in given:
                    entries[i] = tuple(given[role])
                elif role in ('color1', 'color2', 'color') and ci < len(clist):
                    entries[i] = tuple(clist[ci]); ci += 1
        elif kind == 'list':
            count_kw, has_bg = spec.colors[1], spec.colors[2]
            clist = list(colors) if colors else []
            base = 0
            if has_bg:
                entries[0] = tuple(background) if background is not None else _BG_DEFAULT
                base = 1
            for i, c in enumerate(clist[:6-base]):
                entries[base+i] = tuple(c)
            if count_kw and count_kw in spec.words:
                words[spec.words[count_kw]] = max(1, len(clist))
        elif kind == 'rainbow':
            pass  # nessun colore utente

        # memorizza la striscia con l'effetto allegato
        if len(self.strips) >= self.MAX_STRIPS:
            raise ValueError("Raggiunto il massimo di {} strisce.".format(self.MAX_STRIPS))
        start = max(1, min(90, int(round(start))))
        self.strips.append({
            'channel': int(channel), 'start': start,
            'r': 0, 'g': 0, 'b': 0,
            'effect': {'name': spec.name, 'mode': spec.mode,
                       'flags': flag_byte, 'words': words, 'entries': entries},
        })
        return len(self.strips) - 1

    # ---- override della costruzione slot per gestire gli effetti ----
    def build_payload(self):
        p = bytearray(self.base)
        p[self.BRIGHTNESS_OFFSET] = self.brightness & 0xFF
        strips = self._effective_strips()[:self.MAX_STRIPS]

        for k, s in enumerate(strips):
            off = self.SLOT_BASE + k*self.SLOT_SIZE
            fx = s.get('effect')
            if fx:
                slot = self.build_effect_slot(fx['mode'], fx['flags'],
                                              fx['words'], fx['entries'])
            else:
                slot = bytearray(self.SLOT_ACTIVE_TEMPLATE)
                slot[self.OFF_COLOR + 0] = s['g'] & 0xFF
                slot[self.OFF_COLOR + 1] = s['r'] & 0xFF
                slot[self.OFF_COLOR + 2] = s['b'] & 0xFF
            p[off:off + self.SLOT_SIZE] = slot

        # routing identico al motore base
        for i in range(self.ROUTE_BASE, self.ROUTE_BASE + 3*self.MAX_STRIPS):
            p[i] = 0
        records = [(k + 1, s['channel'] - 1, s['start'] - 1)
                   for k, s in enumerate(strips)]
        records.sort(key=lambda rec: (rec[1], -rec[0]))
        for i, (b0, b1, b2) in enumerate(records):
            rec = self.ROUTE_BASE + 3*i
            p[rec + 0] = b0; p[rec + 1] = b1; p[rec + 2] = b2

        lo, hi = self.CRC_RANGE
        p[1664:1666] = self._crc16(p[lo:hi])
        return bytes(p)

    # ---- decoder di comodo per proseguire il reverse engineering ----
    @classmethod
    def decode_slot(cls, slot70):
        s = slot70
        mode = s[1]; flags = s[5]
        words = [s[23+2*k] | (s[23+2*k+1] << 8) for k in range(9)]
        pal = []
        for k in range(6):
            o = cls.PAL_BASE + 4*k
            A, G, R, B = s[o], s[o+1], s[o+2], s[o+3]
            pal.append((R, G, B, A))
        name = EFFECTS[mode].name if mode in EFFECTS else '?'
        return {'mode': mode, 'name': name, 'flags': flags,
                'words': words, 'palette': pal}
