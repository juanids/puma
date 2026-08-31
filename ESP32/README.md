# PUMA Firmware — ESP32-S3 Multi-Electrode Measurement Station

Firmware for the **ESP32-S3** microcontroller dedicated to real-time multi-electrode electrical stimulation, high-speed routing, and synchronized 16-channel data acquisition. It interfaces with a custom multiplexer board, a dual 12-bit DAC stage (**MCP4922** + 2x op-amp buffer), and two 8-channel simultaneous sampling ADCs (**AD7606**).

---

## 🛠️ Hardware Architecture & Peripherals

1. **Multiplexer Shift Registers:**
   - Controls routing and series load resistors across electrode channels via high-speed serial shift registers.
2. **Analog Stimulation (DAC):**
   - **MCP4922** (SPI) paired with an external **2x operational amplifier** stage to scale and buffer the stimulation voltages.
3. **Simultaneous Data Acquisition (ADC):**
   - **2x AD7606 (8-channel each, 16 channels total)** operated via parallel bus reading for microsecond-level synchronization across all electrode nodes.
4. **Range Control:**
   - Dedicated hardware range switching via GPIO (`RAGE`).

---

## 📌 Pinout & Connections (ESP32-S3)

### Multiplexer Control (Shift Registers)
| Signal | ESP32-S3 GPIO | Description |
| :--- | :--- | :--- |
| **SER (Data)** | `GPIO 37` | Serial data input to shift registers |
| **RCLK (Latch)** | `GPIO 36` | Storage register clock / Latch |
| **SRCLK (Clock)** | `GPIO 47` | Shift register clock |

### DAC Stage (MCP4922 + 2x Op-Amp)
| Signal | ESP32-S3 GPIO | Description |
| :--- | :--- | :--- |
| **SCK** | `GPIO 41` | SPI Clock |
| **SDI (MOSI)** | `GPIO 42` | SPI Data |
| **CS** | `GPIO 45` | SPI Chip Select |
| **RAGE** | `GPIO 35` | Measurement range control |

### Dual AD7606 ADC Modules
| Signal | ESP32-S3 GPIO | Description |
| :--- | :--- | :--- |
| **CONVST** | `GPIO 17` | Simultaneous conversion start trigger |
| **RD** | `GPIO 18` | Parallel read strobe |
| **BUSY** | `GPIO 21` | Conversion status indicator |
| **RESET** | `GPIO 38` | Hardware reset line |
| **CS 1** | `GPIO 39` | Chip Select ADC 1 (Channels 0–7) |
| **CS 2** | `GPIO 40` | Chip Select ADC 2 (Channels 8–15) |
| **Parallel Bus** | `GPIO 1` to `GPIO 16` | 16-bit parallel data bus |

---

## ⚡ Serial Command Protocol (`921600 baud`)

The firmware operates as a stateful command processor supporting instant execution and queued execution (up to 100 queued tasks):

| Command / Task | Header | Payload / Arguments | Description |
| :--- | :--- | :--- | :--- |
| **Version Query** | `V` | *None* | Returns the firmware identification string (`PUMA v1.3`). |
| **Queue Reset** | `Q` | *None* | Clears the task buffer and enters queue configuration mode. |
| **Execute Sequence**| `S` | *None* | Sets $T_0$ time reference and executes all queued tasks sequentially. |
| **Resistance Map** | `M` | `m, v, c, d, t` | Performs conductance/resistance mapping across electrode pairs. |
| **I-V Sweep** | `I` | `s0..s7, vmax, cycles, delay, pulses, cota, points, steps2` | Configures multiplexer state, ramps DAC voltage, and monitors activation limits. |
| **Pulse Routine** | `P` | `s0..s7, v1, c1, v2, c2, cycles, delay` | Applies two-stage voltage pulses with specified point durations. |

---

## 🚀 Building & Flashing

- **Framework:** Arduino (ESP32 core) / PlatformIO
- **Baud Rate:** `921600`
- **Required Libraries:**
  - `MCP492X` (DAC communication)
  - `SPI` (Standard ESP32 SPI HAL)
