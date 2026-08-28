# PUMA (Pulse United Multielectrode Analyzer) 🐆

**PUMA** is an open-source hardware and software platform designed to revolutionize the electrical characterization of complex materials, including self-assembled nanowire networks, memristive devices, and in-materia neuromorphic architectures. 

Built around a standard ESP32 microcontroller, dedicated ADCs (AD7606), and DACs (MCP4922), PUMA bridges the gap between high-precision instrumentation and experimental flexibility. It allows researchers to perform multi-terminal measurements, apply arbitrary pulse trains, and monitor transient physical learning events automatically via a user-friendly Python API.

### Key Features
* **16 Independent Terminals:** Full state control (Drive, Ground, or High-Z) for highly localized dynamic routing.
* **Dual Stimulation Channels:** Apply two distinct arbitrary signals simultaneously across the network.
* **High-Precision Output:** 0 to 10 V compliance range with 2.5 mV resolution.
* **Fast Acquisition:** 200 kHz sampling rate to capture rapid transient dynamics.
* **Configurable Hardware Limits:** Independent, manually selectable series resistors (5 kΩ to 10 MΩ) to safely limit compliance currents.
* **Python-Driven Automation:** Plug-and-play scripts to automate I-V sweeps, associative memory protocols, and real-time visualization without needing embedded systems expertise.

This repository contains everything needed to replicate the platform: PCB Gerber files, schematics, ESP32 firmware, and the Python control library.
