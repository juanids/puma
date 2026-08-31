## 🐍 Python Control Software (`control_station.py`)

This directory contains the Python script used to interface with the ESP32-S3 microcontroller via serial communication to automate measurements, stream high-speed multi-terminal data, and sync results.

### Features
* **Routine Management:** Constructs and queues measurement routines:
  * **Resistance Mapping (`CreaMapa`):** Scans conductance/resistance across electrode pairs.
  * **I-V Sweeps (`CreaIV`):** Configures source/ground channels, DAC ramp parameters, series resistors, and activation thresholds.
  * **Pulsing (`CreaP`):** Applies custom multi-stage voltage pulses.
* **Binary Data Streaming & Parsing:** Reads raw binary measurement streams over high-speed UART (`921600 baud`), verifies packet checksums, and parses timestamps and ADC channel values into structured `.csv` files.
* **Cloud Backup:** Automates data synchronization to Google Drive using `rclone`.

### Dependencies
```bash
pip install pyserial numpy matplotlib
