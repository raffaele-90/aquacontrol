# 💧 AquaControl 3.2

### Architecture and project scope

AquaControl is a native control suite for Linux, written specifically for the Aquacomputer ecosystem, programmed for the logic of the Aquaero 6 LT. AquaControl is a program that aims to offer the same features as the official suite for managing custom liquid cooling loops, acting as a Linux alternative to the famous CoolerControl.
CoolerControl is an exceptional software capable of managing countless peripherals but, precisely for this reason, it fails in the goal of specificity offered by this software and its advanced controls.

The software relies on the official Linux kernel driver (`aquacomputer_d5next` by Aleksa Savic) for reading the sensors exposed in `/sys/class/hwmon`. On top of these readings, AquaControl introduces its own independent calculation engine for writing values from 0 to 255 in real time.

### USB Protocol Reverse Engineering

Since the kernel module does not allow modifying the type of power delivery on the board's four 12V outputs, AquaControl integrates a direct communication module via `python-hidapi`. Through reverse engineering of the USB protocol, the software bypasses the kernel to inject targeted payloads (Feature Reports) in real time, allowing the 12V channels to be switched from PWM mode to continuous DC voltage (Power Controlled). The software communicates with the board in override mode in real time, by the author's choice.

## 🚀 AquaControl 3.2 Features

- **Graphical interface and multilingual support**: The GUI is inspired by other software that I consider well-designed with a reasoned organization of functions, conceived to be "user-friendly". To make the software accessible to anyone, it has been translated into Italian, English, German, Spanish, and French, and integrates a manual within the program itself (also translated) to describe the use of the program's advanced features.

- **PWM/DC Hardware Control:** As explained above, hot-switching bypassing kernel limitations.

- **Curve Management and Power Control:** The software allows managing the delivery of each channel through four distinct modes:
  - **Automatic Mode:** Creation of a delivery curve based on user-adjustable parameters (Minimum/maximum temperature, Minimum/maximum power, and Curve/Gamma).
  - **Manual Mode:** Setting the delivery curve point by point via an interactive graph.
  - **PID Mode:** Use of an algorithm (Proportional, Integral, Derivative) to dynamically vary the power delivery to maintain a constant target temperature on a sensor of the user's choice. Includes 3 preset behaviors (*Slow, Normal, Fast*) and a manual mode.
  - **Fixed Mode:** Setting a constant power value.

- **Hysteresis**: Calculates an average temperature value based on values measured over a given time frame (customizable), avoiding the continuous acceleration/deceleration of the fans due to minimal temperature variations.

- **Quick Start (Start Boost):** Greater power is required to start a rotor than the power needed to keep it moving. The "quick start" function allows applying an initial 100% power for a fraction of a second to overcome the rotor's static inertia, then settling to the required power value based on the user's settings.

- **Virtual Sensors (ΔT):** Possibility of creating a virtual sensor calculated on the difference between two sensors. The primary purpose of this function is to be able to use it with an ambient temperature detection sensor coupled with a detection sensor for the liquid temperature. In this way, a curve can be created that regulates the system based on a constant ΔT, decoupling the control of the loop's profiles from the absolute temperature of the liquid, which can vary according to the seasons of the year.

- **Security features:** The software constantly monitors the RPM, power, and voltage values of the four 12V Aquaero outputs, in addition to monitoring the temperature sensors. It is possible to configure critical thresholds at which the system can activate:

  - **Automatic Intervention:** Upon exceeding the threshold, the program intervenes automatically by showing an alarm (visual and auditory), with the possibility of launching a custom command, or forcibly shutting down the PC with root permissions.

  - **Integrated Diagnostics:** In the event of a forced emergency shutdown, the software generates a system log. At the next PC reboot, a popup window will indicate to the user which component caused the anomaly.

  - **Alarm Delay:** Customizable time filter (in seconds) to ignore temporary critical readings, solving the problem of false alarms. This feature was introduced to manage resuming from suspend: upon waking the system, the sensor reading is immediate, but some components (like a D5 pump) require a few moments of time to get back up to speed.

- **On-Screen Display (OSD):** A customizable panel that can be moved anywhere on the desktop. 
**Please note:** Due to Wayland's security rules, the OSD was not designed to overlap game screens in fullscreen mode. The OSD does not aim to replace or overlap dedicated tools like MangoHud, but was born as a system monitoring tool, designed to show sensors during normal desktop work sessions or during windowed stress tests. I have not integrated and do not intend to integrate features that fall outside the scope of the project.

- **Automatic Profile Switch:** AquaControl allows you to create custom profiles and associate them with specific programs (as you would launch them via terminal); it is therefore possible to associate a more aggressive profile when opening a video game or rendering software, with an automatic restoration of the previous profile when the program is closed.


## ⚠️ IMPORTANT WARNING: UPDATING THE FIRMWARE IS NOT RECOMMENDED

The correct operation of the software has been verified and tested on **Aquaero 6 LT boards equipped with Firmware 2104**. Compatibility of the PWM/DC switch on other versions is not guaranteed.

Hardware manufacturers, who do not make their software available on Linux, often release "security fixes" for the sole purpose of changing USB communication protocols and breaking the compatibility of open-source software like this one.

## 🔮 Future Developments

The software is mature enough to control the four 12V outputs of the Aquaero 6 LT. In future versions I plan to integrate:

* **Flow Sensors:** Support for reading data related to flow sensors, which will be converted in the software into flow rate values (liters/hour) with conversion parameters that can be set by the user, based on the chosen sensor. I will obviously also add an option to manage the program's emergency system based on the flow sensor reading.

* **D5 Next Support**

* **Possible support for other Aquacomputer hardware (Beta):** The `aquacomputer_d5next` driver correctly recognizes: Aquaero 5, Aquaero 6, Octo, Quadro, Poweradjust 3, D5 Next, Aquastream XT, Aquastream Ultimate, High Flow Next, High Flow USB, MPS Flow, Leakshield, Farbwerk, and Farbwerk 360. Unfortunately, I do not own any of these peripherals, but it is possible to expand the software's compatibility by putting the features as "Beta" and looking for community Beta testers who physically own these devices and can test the program.


## 🛠 Installation (Arch Linux)

1. Clone this repository to your computer.
2. Open the terminal in the source folder and run the command:
   
   `makepkg -si`
   
The system will compile the package, configure the USB port hardware permissions (udev), apply a Sudoers rule to ensure the emergency shutdown, and install the application automatically resolving the necessary dependencies (such as `python-hidapi`).

3. If you use an NVIDIA graphics card and want to view its load and temperature data, install the additional package from AUR/pacman: 

   `sudo pacman -S python-pynvml`
   
📜 License
Released under the free international GNU GPLv3 license. This is an independent project developed by a user from the Linux community and is in no way affiliated, supported, or endorsed by Aquacomputer.

## 👤 Author / Maintainer

Developed and maintained by **Raffaele Schiavone** ([@raffaele-90](https://github.com/raffaele-90)).

*I write free software because I believe in the right to be able to use the hardware I purchase on the operating system I prefer, without having to install Microsoft Windows.*
