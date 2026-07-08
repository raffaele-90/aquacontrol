# 💧 AquaControl 4.0

<p align="center">
  <img width="100%" alt="AquaControl Desktop Environment" src="https://github.com/user-attachments/assets/efbfd2c3-da86-43a8-8a79-99fb95e6eaa7" />
</p>

### Architecture and project scope

AquaControl is a native Linux control suite, written specifically for the Aquacomputer ecosystem, programmed around the logic of the Aquaero 6 LT and the Farbwerk 360. AquaControl is a program that aims to offer the same features as the official suite for managing custom liquid cooling loops, acting as a Linux alternative to the famous CoolerControl, which supports many more devices but does not offer the advanced controls of this software. Furthermore, AquaControl is currently the only native Linux software that supports Farbwerk 360 LED management.

The software relies in part on the official Linux kernel driver (`aquacomputer_d5next` by Aleksa Savic) to read the sensors exposed in `/sys/class/hwmon`. On top of these readings, AquaControl introduces its own independent calculation engine to write values from 0 to 255 in real time to drive the Aquaero 6 LT.

### USB Protocol Reverse Engineering

Since the kernel module does not provide the ability to change the power delivery mode (PWM/DC) of the board's four 12V channels, nor to manage flow sensor calibration, I used Wireshark to reverse engineer these features and integrated modules for direct communication with the board via `python-hidapi`. Through the same procedure, I managed to make the Farbwerk 360 work and also captured the payload necessary to save the settings to the board's EEPROM.
Unlike the Farbwerk 360, AquaControl does not integrate setting saves to the Aquaero 6 LT's EEPROM, so it works in real-time override mode, by the author's choice.

## 🚀 AquaControl 4.0 Features

<p align="center">
  <img width="100%" alt="AquaControl Dashboard" src="https://github.com/user-attachments/assets/cd41c603-876e-483f-8d31-5eeeb5d0464f" />
</p>

- **Graphical Interface and Multilanguage Support**: The GUI is inspired by other software that I consider well-designed with a reasoned organization of functions, conceived to be "user-friendly". To make the software accessible to everyone, it has been translated into Italian, English, German, Spanish, French, Russian, and simplified Chinese and integrates a manual (also translated) within the program itself, which describes how to use its advanced features.

- **PWM/DC Control:** As explained above, hot-switching bypassing kernel limitations.
- **Flow Sensor Calibration:** Ability to calibrate imp/L values based on the type of sensor used, the coolant, and the fitting type. You can set the parameter manually for sensors not listed, just like in the original software.

- **Curve Management and Power Control:** The software allows you to manage the output of each channel through four distinct modes:
  - **Automatic Mode:** Creation of a delivery curve based on user-set parameters (Min/Max Temperature, Min/Max Power, and Curvature/Gamma).
  - **Manual Mode:** Point-by-point setup of the delivery curve via an interactive graph.
  - **PID Mode:** Use of an algorithm (Proportional, Integral, Derivative) to dynamically vary power delivery in order to maintain a constant target temperature on a user-selected sensor. It includes 3 preset behaviors (*Slow, Normal, Fast*) and a manual mode.
  - **Fixed Mode:** Setting a constant power value.

<p align="center">
  <img width="100%" alt="AquaControl Curve Management" src="https://github.com/user-attachments/assets/e397cf3c-6723-45f8-a2fa-bedb90803626" />
</p>

- **Hysteresis**: Calculates an average temperature value based on measurements over a specified (customizable) timeframe, preventing constant fan acceleration/deceleration due to minimal temperature variations.

- **Start Boost:** More power is needed to start a rotor than to keep it moving. The "start boost" function allows applying an initial 100% power for a fraction of a second to overcome the rotor's static inertia, before settling at the required power value based on user settings.

- **Virtual Sensors (Delta T):** Ability to create a virtual sensor calculated from the difference between two sensors. The primary purpose of this feature is to use it with an ambient temperature sensor paired with a coolant temperature sensor. This allows creating a curve that regulates the system based on a constant Delta T, decoupling the loop's profile control from the absolute coolant temperature, which can vary with the seasons.

- **Flow Sensor Calibration:** The Linux driver reads the flow sensor value in liters per hour; in other words, it does not display the sensor's "raw" value, but rather the value already processed by the board's firmware—either the default setting or one configured via Aquasuite and saved to the EEPROM. Aquacontrol allows you to freely adjust the pulses-per-liter value to match your specific flow sensor, and I have included the same sensors (presets with editable parameters) found in Aquasuite.

- **Safety Features:** The software constantly monitors the RPM, power, and voltage values of the Aquaero's four 12V outputs, as well as monitoring the temperature sensors. You can configure critical thresholds at which the system can activate:

  - **Automatic Intervention:** Upon exceeding the threshold, the program automatically intervenes by displaying an alarm (visual and auditory), with the option to launch a custom command or force a PC shutdown with root privileges.
  - **Integrated Diagnostics:** In the event of a forced emergency shutdown, the software generates a system log. Upon the next PC restart, a popup window will indicate to the user which component caused the anomaly.
  - **Alarm Delay:** A customizable time filter (in seconds) to ignore temporary critical readings, solving the false alarms issue. This feature was introduced to handle waking from suspension: upon system wake, sensor reading is immediate, but some components (like a D5 pump) take a few moments to get up to speed.

<p align="center">
  <img width="100%" alt="AquaControl Security Settings" src="https://github.com/user-attachments/assets/d2a71308-a6c9-48fb-aaf0-a7d37ffdf771" />
</p>

- **On-Screen Display (OSD):** A customizable overlay that can be moved anywhere on the desktop. 
**Please note:** Due to Wayland's security rules, the OSD is not designed to overlay fullscreen game windows. The OSD does not aim to replace or overlay dedicated tools like Mangohud, but was created as a system monitoring tool, designed to show sensors during normal desktop work sessions or windowed stress tests. I have not integrated and do not intend to integrate features that fall outside the project's scope.

- **Automatic Profile Switching:** AquaControl allows you to create custom profiles and link them to specific programs (as you would launch them via terminal); it is therefore possible to associate a more aggressive profile when opening a video game or rendering software, with automatic restoration of the previous profile when the program closes.

- **Farbwerk 360 Support (Partial):**
The Farbwerk 360 is a complex board that integrates numerous features, completely independent and detached from the Aquaero 6 LT, which is instead a board designed for controlling liquid cooling loops. 
Currently, the support is "partial" because AquaControl can manage it as a simple RGB header and I have not integrated further functions beyond RGB LED control. I managed to code the logic of virtual LED strips (20 in total, assignable across the four RGBpx channels) and the setup of several hardware effects. The software is capable of saving settings to the device's EEPROM, so LED configuration changes can survive a system reboot. Unlike Aquasuite, which automatically saves LED configuration settings, this software offers the ability to apply effects without saving them to memory. Farbwerk 360 integration is still under development due to its complexity and the number of features present.

<p align="center">
  <img width="100%" alt="Farbwerk 360 Support" src="https://github.com/user-attachments/assets/6369a3d3-d009-49de-b65f-22688cbfaf64" />
</p>

  - **Fully supported effects:** *Rotating rainbow, Swiping rainbow, Breathing, Color shift, Color change, Blinking, Color sequence, Sequence, Scanner, Laser, Wave, Flame, Rain, Snowfall, Stardust.*

## ⚠️ IMPORTANT WARNING: UPDATING FIRMWARE IS NOT RECOMMENDED

The correct functioning of the software has been verified and tested on **Aquaero 6 LT boards with Firmware 2104** and **Farbwerk 360 boards with Firmware 1025**. Compatibility of features such as the PWM/DC switch and flow sensor calibration is not guaranteed on other firmware versions of the Aquaero 6 LT, just as the functionality of RGB LED control and Farbwerk 360 effects is not guaranteed, because these features were implemented by reverse engineering Aquacomputer's proprietary protocols.
The manufacturer uses closed protocols. Official updates can unpredictably alter the data structure and permanently break compatibility with AquaControl.

## 🛠 Installation

### Arch Linux

1. Clone this repository to your computer by running in the terminal:

   ```bash
   git clone https://github.com/raffaele-90/aquacontrol.git
   ```

2. Open the terminal in the newly cloned source folder and run the command:

   ```bash
   makepkg -si
   ```

   The system will compile the package, configure the USB port hardware permissions (udev), apply a Sudoers rule to grant emergency shutdown, and install the application, automatically resolving necessary dependencies (like `python-hidapi`).

3. If you use an NVIDIA graphics card and want to view its load and temperature data, install the additional package from AUR/pacman: 

   ```bash
   sudo pacman -S python-pynvml
   ```

### Debian / Ubuntu (Coming soon)

1. Download the latest version of the `.deb` package from the [Releases](https://github.com/raffaele-90/aquacontrol/releases) page of the repository.
2. Open the terminal in the folder where you downloaded the file and run:

   ```bash
   sudo apt install ./aquacontrol_*.deb
   ```
   
   *(Note: the exact instructions for udev permissions and any dependencies will be updated upon the official release of the Debian package).*

## 📜 License
Released under the free international GNU GPLv3 license. This is an independent project developed by a Linux community user and is in no way affiliated with, supported by, or endorsed by Aquacomputer.

## 👤 Author / Maintainer

Developed and maintained by **Raffaele Schiavone** ([@raffaele-90](https://github.com/raffaele-90)).
Project repository link: [AquaControl on GitHub](https://github.com/raffaele-90/aquacontrol)

*I write free software because I believe in the right to use the hardware I purchase on the operating system I prefer, without having to install Microsoft Windows.*
