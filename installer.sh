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
#!/bin/bash
# AquaControl - Installatore Universale Linux (v3.1.0)

if [ "$EUID" -ne 0 ]; then
  echo "ERRORE: Per installare AquaControl nel sistema, esegui lo script come root (es. sudo ./installer.sh)"
  exit 1
fi

echo "=> Creazione delle directory di sistema..."
mkdir -p /usr/lib/aquacontrol
mkdir -p /usr/share/applications
mkdir -p /usr/share/icons/hicolor/512x512/apps

echo "=> Copia dei file sorgente Python in /usr/lib..."
cp *.py /usr/lib/aquacontrol/
chmod 644 /usr/lib/aquacontrol/*.py

echo "=> Creazione dell'eseguibile globale in /usr/bin..."
cat << 'EOF' > /usr/bin/aquacontrol
#!/bin/bash
exec python3 /usr/lib/aquacontrol/main.py "$@"
EOF
chmod 755 /usr/bin/aquacontrol

echo "=> Generazione dinamica del lanciatore .desktop..."
cat << 'EOF' > /usr/share/applications/aquacontrol.desktop
[Desktop Entry]
Name=AquaControl
Comment=Suite di controllo per Aquaero 6 LT
Exec=/usr/bin/aquacontrol
Icon=aquacontrol
Terminal=false
Type=Application
Categories=System;HardwareSettings;
EOF
chmod 644 /usr/share/applications/aquacontrol.desktop

echo "=> Installazione dell'icona..."
cp aquacontrol.png /usr/share/icons/hicolor/512x512/apps/
chmod 644 /usr/share/icons/hicolor/512x512/apps/aquacontrol.png

echo "=> Configurazione regole Udev per la porta USB..."
cat << 'EOF' > /etc/udev/rules.d/99-aquaero.rules
# AquaControl - Permessi hardware per Aquaero
SUBSYSTEM=="usb", ATTRS{idVendor}=="0c70", ATTRS{idProduct}=="f001", MODE="0666"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="0c70", ATTRS{idProduct}=="f001", MODE="0666"
EOF
chmod 644 /etc/udev/rules.d/99-aquaero.rules

echo "=> Applicazione immediata dei permessi hardware..."
AQUAERO_FOUND=0
for hwmon in /sys/class/hwmon/hwmon*; do
    if [ -f "$hwmon/name" ] && grep -q "aquaero" "$hwmon/name"; then
        chmod a+w "$hwmon"/pwm* 2>/dev/null
        echo "   Permessi di scrittura concessi su: $hwmon"
        AQUAERO_FOUND=1
    fi
done

if [ "$AQUAERO_FOUND" -eq 0 ]; then
    echo "   ATTENZIONE: Nessun Aquaero rilevato attualmente nel sistema."
fi

echo "=> Configurazione regole Polkit per lo spegnimento di emergenza..."
mkdir -p /etc/polkit-1/rules.d
cat << 'EOF' > /etc/polkit-1/rules.d/99-aquacontrol-shutdown.rules
/* Consente agli utenti del gruppo wheel di forzare lo spegnimento ignorando gli inhibitor */
polkit.addRule(function(action, subject) {
    if (action.id == "org.freedesktop.login1.power-off" ||
        action.id == "org.freedesktop.login1.power-off-multiple-sessions" ||
        action.id == "org.freedesktop.login1.power-off-ignore-inhibit") {
        if (subject.isInGroup("wheel")) {
            return polkit.Result.YES;
        }
    }
});
EOF
chmod 644 /etc/polkit-1/rules.d/99-aquacontrol-shutdown.rules

echo "=> Aggiornamento dei demoni di sistema e cache icone..."
udevadm control --reload-rules
udevadm trigger
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor > /dev/null 2>&1
fi

echo "=> Installazione completata con successo! Puoi avviare AquaControl dal menu applicazioni."
