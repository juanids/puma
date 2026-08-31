# Placa de Medición Multielectrodo — Etapa de Multiplexión

Este directorio contiene los archivos de fabricación y ensamble de KiCad correspondientes a la **sección de multiplexión** del sistema de medición multielectrodo.

---

## 📁 Contenido de la carpeta

- **Gerbers (`/gerber` o `.zip`):** Archivos de capas de cobre, máscara de soldadura, serigrafía y perforaciones (Drill) para fabricación de la PCB.
- **BOM (`bill_of_materials.csv`):** Lista completa de componentes, encapsulados y referencias de diseño.
- **CPL / Centroid (`positions.csv`):** Archivo de coordenadas y orientación de componentes Pick & Place para ensamble SMT.

---

## ⚙️ Conexión y Control (ESP32-S3)

La placa está diseñada para controlarse mediante un microcontrolador **ESP32-S3**. Los pines de comunicación y control deben configurarse de la siguiente manera:

| Función | Pin en PCB | Pin ESP32-S3 | Notas |
| :--- | :--- | :--- | :--- |
| **SCK** | Reloj SPI | **GPIO 36** | Línea de clock |
| **MOSI** | Datos SPI | **GPIO 37** | Salida de datos del master |
| **LR** | Latch / Load | **GPIO 47** | **Todos los pines LR deben estar cortocircuitados entre sí** |

---

## ⚡ Alimentación

- **Fuentes requeridas:** 
  - `+5 V`
  - `-5 V`
  - `+12 V`
- **Masa:** Todas las referencias de tierra (**GND**) de las distintas fuentes deben estar **cortocircuitadas** a un punto de referencia común.
- **Alimentación analógica / Señal de estímulo:** Conectar a una fuente con DAC (se sugiere el uso de un **MCP4922** o equivalente).

---

## 🔌 Salidas y Ruteo de Electrodos

- **`I1` a `I16`:** Salidas directas de los 16 electrodos (**sin buffer**).
- **Salidas superiores:** Salidas correspondientes a los canales con etapa de adaptación / **buffereadas**.
