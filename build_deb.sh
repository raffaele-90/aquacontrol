#!/bin/bash
#
# build_deb.sh
# Script per la creazione automatizzata del pacchetto .deb per AquaControl
#

set -e

PKGNAME="aquacontrol"
PKGVER="4.0.2"
ARCH="all"
BUILD_DIR="${PKGNAME}_${PKGVER}_${ARCH}"

echo "==> Pulizia di build precedenti..."
rm -rf "${BUILD_DIR}"
rm -f "${BUILD_DIR}.deb"

echo "==> Creazione della struttura delle directory..."
mkdir -p "${BUILD_DIR}/usr/lib/${PKGNAME}"
mkdir -p "${BUILD_DIR}/usr/bin"
mkdir -p "${BUILD_DIR}/usr/share/applications"
mkdir -p "${BUILD_DIR}/usr/share/icons/hicolor/512x512/apps"
mkdir -p "${BUILD_DIR}/etc/udev/rules.d"
mkdir -p "${BUILD_DIR}/etc/sudoers.d"
mkdir -p "${BUILD_DIR}/DEBIAN"

echo "==> Copia dei file sorgenti Python e Assets..."
cp *.py "${BUILD_DIR}/usr/lib/${PKGNAME}/"
cp -r assets "${BUILD_DIR}/usr/lib/${PKGNAME}/"
find "${BUILD_DIR}/usr/lib/${PKGNAME}/assets" -type d -exec chmod 755 {} +
find "${BUILD_DIR}/usr/lib/${PKGNAME}/assets" -type f -exec chmod 644 {} +

echo "==> Generazione del wrapper eseguibile..."
cat << 'EOF' > "${BUILD_DIR}/usr/bin/${PKGNAME}"
#!/bin/bash
exec python3 /usr/lib/aquacontrol/main.py "$@"
EOF
chmod 755 "${BUILD_DIR}/usr/bin/${PKGNAME}"

echo "==> Copia dell'icona..."
cp aquacontrol.png "${BUILD_DIR}/usr/share/icons/hicolor/512x512/apps/"
chmod 644 "${BUILD_DIR}/usr/share/icons/hicolor/512x512/apps/aquacontrol.png"

echo "==> Generazione del file .desktop..."
cat << EOF > "${BUILD_DIR}/usr/share/applications/${PKGNAME}.desktop"
[Desktop Entry]
Name=AquaControl
Comment=Control suite for Aquaero 6 LT and Farbwerk 360
Comment[it]=Suite di controllo per Aquaero 6 LT e Farbwerk 360
Comment[fr]=Suite de contrôle pour Aquaero 6 LT et Farbwerk 360
Comment[es]=Suite de control para Aquaero 6 LT y Farbwerk 360
Comment[de]=Steuerungssuite für Aquaero 6 LT und Farbwerk 360
Comment[ru]=Пакет управления для Aquaero 6 LT и Farbwerk 360
Comment[zh_CN]=Aquaero 6 LT 和 Farbwerk 360 控制套件
Exec=/usr/bin/${PKGNAME}
Icon=${PKGNAME}
Terminal=false
Type=Application
Categories=System;HardwareSettings;
EOF
chmod 644 "${BUILD_DIR}/usr/share/applications/${PKGNAME}.desktop"

echo "==> Generazione delle regole UDEV..."
cat << 'EOF' > "${BUILD_DIR}/etc/udev/rules.d/99-aquaero.rules"
# AquaControl - Permessi hardware per Aquaero 6 LT e Farbwerk 360
SUBSYSTEM=="usb", ATTRS{idVendor}=="0c70", ATTRS{idProduct}=="f001", MODE="0666"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="0c70", ATTRS{idProduct}=="f001", MODE="0666"
SUBSYSTEM=="usb", ATTRS{idVendor}=="0c70", ATTRS{idProduct}=="f010", MODE="0666"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="0c70", ATTRS{idProduct}=="f010", MODE="0666"
ACTION=="add", SUBSYSTEM=="hwmon", ATTRS{name}=="aquaero", RUN+="/bin/sh -c 'chmod a+w /sys$devpath/pwm*'"
EOF
chmod 644 "${BUILD_DIR}/etc/udev/rules.d/99-aquaero.rules"

echo "==> Generazione delle regole Sudoers per Debian/Ubuntu..."
cat << 'EOF' > "${BUILD_DIR}/etc/sudoers.d/99-aquacontrol-shutdown"
# AquaControl - Spegnimento di emergenza
%sudo ALL=(ALL) NOPASSWD: /usr/bin/systemctl poweroff --force --force
EOF
chmod 440 "${BUILD_DIR}/etc/sudoers.d/99-aquacontrol-shutdown"

echo "==> Generazione del file DEBIAN/control..."
cat << EOF > "${BUILD_DIR}/DEBIAN/control"
Package: ${PKGNAME}
Version: ${PKGVER}
Section: utils
Priority: optional
Architecture: ${ARCH}
Depends: python3, python3-pyside6, python3-hid
Maintainer: Raffaele Schiavone <raffaele-90@github.com>
Description: Control suite for Aquaero 6 LT and Farbwerk 360
 AquaControl is a native Linux control suite, written specifically for the
 Aquacomputer ecosystem, programmed around the logic of the Aquaero 6 LT
 and the Farbwerk 360.
EOF
chmod 644 "${BUILD_DIR}/DEBIAN/control"

echo "==> Generazione degli script DEBIAN/postinst..."
cat << 'EOF' > "${BUILD_DIR}/DEBIAN/postinst"
#!/bin/sh
set -e
# Ricarica le regole udev e aggiorna la cache delle applicazioni desktop
udevadm control --reload-rules || true
udevadm trigger || true
update-desktop-database /usr/share/applications || true
EOF
chmod 755 "${BUILD_DIR}/DEBIAN/postinst"

echo "==> Costruzione del pacchetto .deb..."
dpkg-deb --root-owner-group --build "${BUILD_DIR}"

echo "==> Pulizia della directory temporanea..."
rm -rf "${BUILD_DIR}"

echo "==> Completato! Pacchetto generato: ${BUILD_DIR}.deb"
