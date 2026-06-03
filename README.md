# 💧 AquaControl 3.1

### Architecture and project scope

AquaControl is a native control suite for Linux, written specifically for the Aquacomputer ecosystem, programmed for the logic of the Aquaero 6 LT. Aquacontrol is a program that aims to offer the same functionalities as the official suite for managing custom liquid cooling loops, a linux alternative to the famous CoolerControl.
CoolerControl is exceptional software capable of managing countless peripherals but, precisely for this reason, fails in the goal of specificity offered by this software and its advanced controls.

The software relies on the official Linux kernel driver (aquacomputer_d5next by Aleksa Savic) to read the sensors exposed in /sys/class/hwmon. On top of these readings, AquaControl introduces its independent calculation engine for writing values from 0 to 255 in real time.

### Reverse Engineering of the USB Protocol

Since the kernel module does not allow modifying the type of current delivery on the four 12v outputs of the board, AquaControl integrates a direct communication module via python-hidapi. Through reverse engineering of the USB protocol, the software bypasses the kernel to inject targeted payloads (Feature Reports) in real time, allowing the 12V channels to be switched from PWM mode to continuous DC voltage (Power Controlled). The software communicates with the board in override mode in real time, by the author's choice.

## 🚀 AquaControl 3.1 Features

- **Graphical interface and multilingual support**: The graphical interface is inspired by that of other software that I consider well designed with a reasoned organization of functions, conceived to be "user friendly". To make the software accessible to anyone, it has been translated into Italian, English, German, Spanish and French and integrates within the program itself a manual (also translated) to describe the use of the advanced functions of the program.

- **PWM/DC Hardware Control:** As explained above, hot switch bypassing kernel limitations.

- **Hysteresis**: Calculates an average temperature value based on the values measured in a certain period of time (customizable) avoiding the continuous acceleration/deceleration of the fans due to minimal temperature variations.

- **Quick Start (Start Boost):** Due to the mechanical inertia of the fans, more power is needed to start a fan, compared to the power needed to keep it rotating. The "quick start" function allows you to apply a maximum initial power of 100% for a fraction of a second to overcome mechanical stall, and then apply a minimum power value that allows the fans to keep spinning, based on the settings chosen by the user.

- **Temperature Maintenance (PID Algorithm):** Maintenance of a constant target temperature on a sensor of the user's choice.
Includes 3 preset behaviors (*Slow, Normal, Fast*) and a manual mode.

- **Virtual Sensors (Delta T):** Possibility to create a virtual sensor calculated on the difference between two sensors. The primary purpose of this function is to be able to use it with an ambient temperature detection sensor coupled with a sensor for detecting liquid temperatures. In this way a curve can be created that regulates the system based on a constant Delta T, untying the control of the system's profiles from the absolute temperature of the liquid, which can vary based on the seasons of the year.

- **Security functions and alarms:** The software constantly monitors the RPM, power and voltage values of the four 12v Aquaero outputs, as well as monitoring the temperature sensors. It is possible to configure critical thresholds, in which the program can intervene automatically showing an alarm (visual and auditory) by forcibly shutting down the pc with root permissions and/or launching a custom command of the user's choice.

- **On-Screen Overlay (OSD):** A customizable panel that can be moved anywhere on the desktop. 

**Please note:** Due to Wayland's security rules, the OSD was not designed to overlay game screens in fullscreen mode. The OSD does not aim to replace or overlap dedicated tools like Mangohud, but was born as a system monitoring tool, designed to show system and aquaero sensors, during normal desktop work sessions, during the use of benchmarks or windowed stress tests. I have not integrated and do not intend to integrate functions that fall outside the scope of the project.

- **Automatic Profile Switch:** AquaControl allows you to create custom profiles and associate them with specific programs (as you would start them via terminal); it is therefore possible to associate a more aggressive profile when opening a videogame or rendering software, with automatic restoration of the previous profile upon closing the program.


## ⚠️ IMPORTANT WARNING: UPDATING THE FIRMWARE IS NOT RECOMMENDED

The correct functioning of the software has been verified and tested on **Aquaero 6LT boards equipped with Firmware 2104**. Compatibility of the PWM/DC switch on other versions is not guaranteed.

Often hardware manufacturers, who do not make their software available on Linux, release "security fixes" for the sole purpose of changing usb communication protocols and breaking the compatibility of opensource software like this.

## 🔮 Future Developments

The software is mature enough for the control of the four 12v outputs of Aquaero 6 LT. In upcoming versions I plan to integrate:

* **Flow Sensors:** Support for reading data related to flow sensors, which will be converted in the software into liquid flow values (liters/hour) with conversion parameters that can be set by the user, based on the chosen sensor. Obviously I will also add an option to manage the program's emergency system based on the flow sensor reading.

* **D5 Next Support**

* **Possible for other Aquacomputer hardware (Beta):** The aquacomputer_d5next driver correctly recognizes: Aquaero 5, Aquaero 6, Octo, Quadro, Poweradjust 3, D5 Next, Aquastream XT, Aquastream Ultimate, High Flow Next, High Flow USB, MPS Flow, Leakshield, Farbwerk and Farbwerk 360. Unfortunately I do not own any of these peripherals, but it is possible to expand the compatibility of the software by putting the features as "Beta" and looking for Beta testers from the community who physically own these devices and can test the program.


## 🛠 Installation (Arch Linux)

1. Clone this repository on your computer.
2. Open the terminal in the sources folder and run the command:
   
   `makepkg -si`
   
The system will compile the package, configure the hardware permissions of the USB port (udev) and install the application automatically resolving the necessary dependencies (like python-hidapi).

3. If you use an NVIDIA video card and wish to display its load and temperature data, install the additional package from AUR/pacman: 

   `sudo pacman -S python-pynvml`
   
📜 License
Released under the free international GNU GPLv3 license. This is an independent project developed by a user from the Linux community and is in no way affiliated with, supported or approved by Aquacomputer.

## 👤 Author / Maintainer

Developed and maintained by **Raffaele Schiavone** ([@raffaele-90](https://github.com/raffaele-90)).

*I write free software because I believe in the right to be able to use the hardware I purchase on the operating system I prefer, without having to install Microsoft Windows.*
