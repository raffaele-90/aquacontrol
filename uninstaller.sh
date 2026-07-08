#!/bin/bash
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

# AquaControl - Uninstaller Universale Linux (v4.0)

if [ "$EUID" -ne 0 ]; then
  echo "ERRORE: Per disinstallare AquaControl, esegui lo script come root (es. sudo ./uninstaller.sh)"
  exit 1
fi

echo "=> Rimozione dei file eseguibili e librerie..."
rm -rf /usr/lib/aquacontrol
rm -f /usr/bin/aquacontrol

echo "=> Rimozione del lanciatore e dell'icona..."
rm -f /usr/share/applications/aquacontrol.desktop
rm -f /usr/share/icons/hicolor/512x512/apps/aquacontrol.png

echo "=> Rimozione delle regole di sistema (udev e sudoers)..."
rm -f /etc/udev/rules.d/99-aquaero.rules
rm -f /etc/sudoers.d/99-aquacontrol-shutdown

echo "=> Aggiornamento dei demoni di sistema e cache..."
udevadm control --reload-rules
udevadm trigger

if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor > /dev/null 2>&1
fi

echo "=> Disinstallazione di sistema completata!"
echo "Nota: I tuoi profili personali in ~/.config/aquacontrol non sono stati eliminati."
