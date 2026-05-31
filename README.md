*🇮🇹 [Leggi la documentazione in Italiano](README.it.md)*

# 💧 OpenAquaero 3.0

OpenAquaero is an open-source, native, and lightweight software for Linux, specifically designed to manage the **Aquacomputer Aquaero 6 LT** board. It offers a modern and focused interface for controlling custom liquid cooling loops directly from your Linux desktop, without having to rely on virtual machines or proprietary software.

The program operates in **real-time override** mode: it constantly communicates with the board via USB to regulate its behavior moment by moment, without writing to or wearing out the device's internal ROM memory. This ensures flexible, secure control that is perfectly integrated with the operating system.

## 🚀 OpenAquaero 3.0 Features

OpenAquaero introduces advanced and intuitive loop management, designed for all users, offering a guide to advanced features directly integrated within the software.

- **Direct Hardware Control (PWM/DC):** The software communicates directly with the hardware via the USB port. It allows you to change the type of signal sent to each individual channel (PWM or DC) in real time. This feature is crucial for properly managing pumps or older 3-pin fans that lack PWM control, by directly regulating their voltage.
- **Temperature Maintenance (PID Algorithm):** Instead of configuring rigid curves based on graph points, you can define a target temperature for your coolant (e.g., 40°C). The software uses a smart calculation system that constantly adapts the speed of fans and pumps based on the PC's instantaneous load, preventing the coolant from exceeding the set threshold. It includes 3 preset behaviors (*Slow, Normal, Fast*) and a manual mode.
- **Virtual Sensors (Delta T):** This feature allows you to create a smart sensor based on the temperature difference between two points in the loop. The ideal use case consists of subtracting the temperature from an ambient room sensor from the coolant temperature. This provides a constant dissipation value across every season: the system will avoid running fans at 100% in the summer to chase physically impossible temperatures, ensuring the same acoustic silence in January as in August.
- **Physical Limits and Start Boost:** Many pumps and fans cannot spin if they receive too low a power percentage, risking a mechanical stall. With this feature, you can set a minimum power under which the channel turns off completely. Furthermore, by activating *Start boost*, the software will provide an initial 100% kick for a fraction of a second whenever a stationary fan needs to start, overcoming the initial inertia of the blades.
- **On-Screen Display (OSD) and Anti-Bloatware Philosophy:** A floating, transparent, and customizable info panel that shows the status of fans and temperatures on the desktop in real time. **Please note:** due to the strict security rules of modern display servers (like Wayland), the OSD is not designed to overlay games in fullscreen mode. This software is not meant to replace specific gaming tools like *MangoHud* (which remains the ideal choice for monitoring fps and in-game sensors), but rather to keep an eye on the loop during stress-test sessions, benchmarking, or as a simple daily desktop monitor. OpenAquaero embraces the open-source philosophy of "do one thing and do it well", so it doesn't integrate features known from other programs that fall outside the project's scope.
- **Automatic Profile Switching:** OpenAquaero detects the programs running on your computer. You can link profiles to specific applications, allowing the system to automatically load your most aggressive cooling profile when launching a specific game or rendering software, and then automatically restore the previous profile as soon as the program is closed.

## ⚠️ CRITICAL WARNING: DO NOT UPDATE THE FIRMWARE

The proper functioning of this software has been verified and tested on **Aquaero 6LT boards equipped with Firmware 2104**. Compatibility of the advanced USB communication features is not guaranteed with different firmware versions.

**IT IS STRONGLY ADVISED NOT TO UPDATE THE BOARD'S FIRMWARE.**

Hardware manufacturers often release management tools exclusively for Microsoft Windows, ignoring the existence of free platforms and forcing users to endure commercial operating systems that track and monetize personal data. When independent developers dedicate months of free work to reverse engineering to give users back the right to use the hardware they purchased on free systems like Linux, companies respond by releasing fake "security updates".

These updates often have the sole purpose of arbitrarily modifying the board's internal codes and communication protocols, intentionally breaking compatibility with alternative community software. If you spent over €150 on a premium hardware controller, you have the absolute right to use it on the operating system of your choice. To prevent your board from turning into an expensive paperweight on Linux, we urge you not to apply official firmware updates. If the manufacturer wishes to counter these projects, they are free to release an official, native version of their suite for Linux; until then, the community will continue to defend hardware freedom.

## 🔮 Future Developments

The software is fully mature for the daily control of even the most complex cooling systems. In upcoming releases, we plan to integrate:
* **Flow Sensors:** Support for reading liquid flow rate data (liters/hour) to monitor pump health and waterblock efficiency.
* **Farbwerk 360 Support:** Researching the creation of an integrated software module or a lightweight external dependency capable of interfacing with dedicated RGB controllers, extending PC lighting control directly from Linux in harmony with the open-source ecosystem (like OpenRGB).

## 🛠 Installation (Arch Linux)

1. Clone this repository to your computer.
2. Open the terminal in the project folder and run the command:
   
   `makepkg -si`
   
The system will build the package, configure the necessary USB hardware permissions (udev), and install the application, automatically resolving the required dependencies (such as python-hidapi).

3. If you use an NVIDIA graphics card and want to display its load and temperature data, install the additional package from AUR/pacman: 

   `sudo pacman -S python-pynvml`
   
## 📜 License
Released under the free international **GNU GPLv3** license. This is an independent project developed by the Linux user community and is in no way affiliated with, supported by, or endorsed by Aquacomputer.
