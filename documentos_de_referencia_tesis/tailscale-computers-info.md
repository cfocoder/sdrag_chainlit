# Información de Computadoras Tailscale

**Última actualización:** 20 de diciembre de 2025

## Red Tailscale

| Máquina | IP Tailscale | Estado | Usuario | SO |
|---------|--------------|--------|---------|-----|
| vostro | 100.116.107.52 | ✅ Activa (Local) | cfocoder@ | Linux |
| cfocoder3 | 100.105.68.15 | ✅ Activa | cfocoder@ | Linux |
| macmini | 100.110.109.43 | ✅ Activa | cfocoder@ | Linux |
| inspiron13windows | 100.65.52.49 | ⚠️ Offline (21h) | cfocoder@ | Windows |
| inspiron13wsl | 100.120.133.19 | ⚠️ Offline (1d) | cfocoder@ | Linux (WSL2) |
| inspiron15 | 100.97.3.35 | ✅ Activa | cfocoder@ | Windows |
| inspiron15wsl | 100.96.32.5 | ⚠️ Offline (15h) | cfocoder@ | Linux (WSL2) |

---

## 1. VOSTRO (100.116.107.52) - Máquina Local ✅

### Información del Hardware
- **Fabricante:** Dell Inc.
- **Modelo:** Vostro 14-3468
- **Serie:** Vostro
- **SKU:** 0792
- **Serial Number:** JGDX5L2
- **Service Tag:** JGDX5L2
- **UUID:** 4c4c4544-0047-4410-8058-cac04f354c32
- **Asset Tag:** No especificado
- **BIOS:** Dell Inc. v3.6.0 (30/06/2020)
- **Año:** ~2017 (CPU 7ma generación Intel)

### Sistema Operativo
- **OS:** Ubuntu 24.04.3 LTS (Noble Numbat)
- **Kernel:** 6.14.0-37-generic
- **Hostname:** hectorsa-Vostro-14-3468
- **Arquitectura:** x86_64

### CPU
- **Modelo:** Intel(R) Core(TM) i5-7200U @ 2.50GHz
- **Núcleos:** 2 cores, 4 threads (2 threads por core)
- **Sockets:** 1
- **Frecuencia:**
  - Mínima: 400 MHz
  - Máxima: 3100 MHz
- **NUMA:** node0 (CPUs 0-3)

### Memoria RAM ✨ **UPGRADED!**
- **Total Instalada:** 32 GB (31 GiB usable)
- **Usada:** 6.3 GiB
- **Libre:** 20 GiB
- **Compartida:** 656 MiB
- **Buffer/Cache:** 5.3 GiB
- **Disponible:** 24 GiB
- **Swap:** 4.0 GiB (0 usado)

#### Especificaciones Técnicas RAM
- **Tipo:** DDR4 SODIMM
- **Velocidad Nominal:** 3200 MT/s
- **Velocidad Configurada:** 2133 MT/s (limitado por CPU i5-7200U)
- **Voltaje:** 1.2V
- **Data Width:** 64 bits
- **Form Factor:** SO-DIMM (laptop)
- **Corrección de Errores:** No (sin ECC)

#### Configuración Actual (2025)
- **Slot DIMM A (BANK 0):**
  - 16 GB DDR4-3200
  - Fabricante: 04CB000002B5
  - Part Number: AX4S320016G22-SBHN
  - Velocidad configurada: 2133 MT/s

- **Slot DIMM B (BANK 2):**
  - 16 GB DDR4-3200
  - Fabricante: 04CB000002B5
  - Part Number: AX4S320016G22-SBHN
  - Velocidad configurada: 2133 MT/s

#### Capacidad Máxima ✅
- **Máxima Capacidad Soportada:** 32 GB
- **Número de Slots:** 2 (ambos ocupados)
- **Estado:** ✅ **MÁXIMA CAPACIDAD ALCANZADA**

**Nota:** Los módulos son DDR4-3200, pero el CPU i5-7200U (7ma gen) solo soporta hasta 2133 MT/s, por lo que funcionan a esa velocidad. Esto es normal y proporciona máxima compatibilidad.

### GPU
- **Modelo:** Intel Corporation HD Graphics 620 (rev 02)
- **Tipo:** VGA compatible controller integrado
- **Bus:** 00:02.0

### Almacenamiento

#### Disco Principal (SSD) ✨
- **Dispositivo:** /dev/sda (931.5 GB total)
- **Tipo:** **SSD** (ROTA=0)
- **Modelo:** WDC WDS100T2G0A-00JH30 (Western Digital Green 1TB)
- **Granularidad:** 512B
- **Particiones:**
  - `/dev/sda1` - 1 GB (EFI Boot) - montado en `/boot/efi`
  - `/dev/sda2` - 930.5 GB (Sistema) - montado en `/`

#### Uso de Disco
- **Filesystem:** /dev/sda2
- **Tamaño:** 915 GB
- **Usado:** 424 GB (49%)
- **Disponible:** 445 GB

#### Unidad Óptica
- **Modelo:** HL-DT-ST DVD+/-RW GU90N

### Estado del Sistema
- **Uptime:** 4 minutos (al momento de la captura)
- **Load Average:** 3.16, 2.12, 0.94
- **Usuarios conectados:** 3

### Dispositivos Adicionales
- **CD/DVD ROM:** sr0 (1024M)
- **Snaps instalados:** Múltiples aplicaciones (Firefox, GIMP, Thunderbird, OnlyOffice, Inkscape, etc.)

---

## 2. CFOCODER3 (100.105.68.15) ✅

**Estado de conexión:** Activa (direct 158.101.44.18:60743)

### Información del Hardware
- **Tipo:** Máquina Virtual (KVM)
- **Proveedor:** Oracle Cloud Infrastructure (OCI)
- **Plan:** **Always Free Tier** ☁️ (Free Forever)
- **Shape:** VM.Standard.A1.Flex (ARM Ampere)
- **Hypervisor:** QEMU/KVM virt-7.2
- **Serial Number:** No especificado (instancia cloud)
- **UUID:** 51a76132-cf63-43c3-9357-b11b433a485c
- **Asset Tag:** OracleCloud.com
- **Año:** Instancia de nube (provisionada según demanda)

### Sistema Operativo
- **OS:** Ubuntu 24.04.3 LTS (Noble Numbat)
- **Kernel:** 6.14.0-1018-oracle
- **Hostname:** cfocoder3
- **Arquitectura:** aarch64 (ARM64)

### CPU
- **Modelo:** ARM Neoverse-N1
- **Vendor:** ARM
- **Núcleos:** 4 cores (1 thread por core)
- **Sockets:** 1
- **Stepping:** r3p1
- **BogoMIPS:** 50.00
- **NUMA:** node0 (CPUs 0-3)

### Características de Seguridad
- ✅ No afectado por: Gather data sampling
- ✅ No afectado por: Ghostwrite
- ✅ No afectado por: Indirect target selection
- ✅ No afectado por: Itlb multihit

### Memoria RAM
- **Total Instalada:** 24 GB (23 GiB usable)
- **Usada:** 7.4 GiB
- **Libre:** 5.0 GiB
- **Compartida:** 370 MiB
- **Buffer/Cache:** 11 GiB
- **Disponible:** 15 GiB
- **Swap:** 0 B (sin swap configurado)

#### Especificaciones Técnicas RAM (Virtual)
- **Tipo:** RAM virtualizada (QEMU/KVM)
- **Form Factor:** DIMM (virtual)
- **Corrección de Errores:** Multi-bit ECC
- **Máxima Capacidad:** 24 GB (configuración actual)

#### Configuración Actual
- **DIMM 0:** 16 GB (virtualizado)
- **DIMM 1:** 8 GB (virtualizado)
- **Fabricante:** QEMU (hypervisor)

**Nota:** Como instancia cloud, la RAM se escala dinámicamente según el shape seleccionado

### GPU
- **GPU dedicada:** No detectada (servidor en nube Oracle Cloud)
- **Tipo:** Instancia ARM en la nube

### Almacenamiento

#### Disco Principal (Sistema) - Block Volume
- **Dispositivo:** /dev/sda (46.6 GB total)
- **Tipo:** Block Volume (Oracle Cloud Storage)
- **Modelo:** BlockVolume (virtualizado)
- **Granularidad:** 32KB
- **Particiones:**
  - `/dev/sda1` - 45.6 GB (Sistema) - montado en `/`
  - `/dev/sda15` - 99 MB (EFI Boot) - montado en `/boot/efi`
  - `/dev/sda16` - 923 MB (Boot) - montado en `/boot`

#### Disco Secundario (Almacenamiento) - Block Volume
- **Dispositivo:** /dev/sdb (151 GB total)
- **Tipo:** Block Volume (Oracle Cloud Storage)
- **Modelo:** BlockVolume (virtualizado)
- **Granularidad:** 32KB
- **Particiones:**
  - `/dev/sdb1` - 151 GB - montado en `/mnt/myvolume`

#### Uso de Disco
- **Filesystem raíz:** /dev/sda1
- **Tamaño:** 45 GB
- **Usado:** 28 GB (62%)
- **Disponible:** 17 GB

**Nota:** Los Block Volumes de Oracle Cloud son almacenamiento de alto rendimiento basado en NVMe

### Estado del Sistema
- **Uptime:** 1 día, 12 minutos
- **Load Average:** 0.46, 0.64, 0.63
- **Usuarios conectados:** 6

### Dispositivos Adicionales
- **Snaps instalados:** core18, oracle-cloud-agent, snapd
- **Usuario SSH:** ubuntu

### Notas Especiales
- 🏢 Instancia en **Oracle Cloud** (arquitectura ARM)
- ☁️ **Always Free Tier** - Recursos garantizados sin costo:
  - 4 ARM cores (Ampere A1)
  - 24 GB RAM
  - 200 GB almacenamiento total (Block Volumes)
  - 10 TB transferencia/mes
  - Sin cargo mensual permanentemente
- 🔧 Kernel Oracle específico para la nube
- 💾 Volumen adicional montado en `/mnt/myvolume` (151 GB)
- ⚡ Excelente para procesamiento 24/7 sin costo

---

## 3. MACMINI (100.110.109.43) ✅

**Estado de conexión:** Activa (direct 192.168.1.23:41641)

### Información del Hardware
- **Fabricante:** Apple Inc.
- **Modelo:** Mac mini 6,1 (Late 2012)
- **Serie:** Macmini
- **Serial Number:** C07LC2B2DWYL
- **UUID:** 8a16494d-b00e-c459-bfff-0d5f5e32b349
- **Asset Tag:** No especificado
- **BIOS:** Apple Inc. v286.0.0.0.0 (10/06/2020)
- **Año:** 2012 (finales de 2012)

### Sistema Operativo
- **OS:** Ubuntu 24.04.3 LTS (Noble Numbat)
- **Kernel:** 6.14.0-36-generic
- **Hostname:** hector-Macmini6-1
- **Arquitectura:** x86_64

### CPU
- **Modelo:** Intel(R) Core(TM) i5-3210M @ 2.50GHz
- **Familia:** Intel Core (3ra Generación - Ivy Bridge)
- **Núcleos:** 2 cores, 4 threads (2 threads por core)
- **Sockets:** 1
- **Frecuencia:**
  - Mínima: 1200 MHz
  - Máxima: 3100 MHz
  - Actual: 93%
- **BogoMIPS:** 4988.49
- **Virtualización:** VT-x habilitado

### Memoria RAM
- **Total Instalada:** 16 GB (15 GiB usable)
- **Usada:** 7.3 GiB
- **Libre:** 1.2 GiB
- **Compartida:** 180 MiB
- **Buffer/Cache:** 7.7 GiB
- **Disponible:** 8.2 GiB
- **Swap:** 4.0 GiB (2.2 GiB usado, 1.8 GiB libre)

#### Especificaciones Técnicas RAM
- **Tipo:** DDR3 SODIMM
- **Velocidad:** 1333 MT/s (PC3-10600)
- **Form Factor:** SO-DIMM (laptop)
- **Corrección de Errores:** No (sin ECC)
- **Máxima Capacidad Soportada:** 8 GB (oficial Apple)

#### Configuración Actual
- **DIMM 0 (BANK 0):** 8 GB DDR3-1333
- **DIMM 0 (BANK 1):** 8 GB DDR3-1333
- **Fabricante:** 0x0198 (Micron/Crucial)
- **Part Number:** 0x393955353432382D3036382E4130304C4620

**⚠️ Nota:** Este Mac mini 2012 está al límite de RAM (16GB no oficial, 8GB oficial). No se recomienda más upgrade

### GPU
- **Modelo:** Intel Corporation 3rd Gen Core processor Graphics Controller (rev 09)
- **Tipo:** VGA compatible controller integrado
- **Bus:** 00:02.0

### Almacenamiento

#### Disco Principal (Sistema) - SSD ✨
- **Dispositivo:** /dev/sda (447.1 GB total)
- **Tipo:** **SSD** (ROTA=0)
- **Modelo:** WD Green 2.5" 480GB
- **Granularidad:** 512B
- **Particiones:**
  - `/dev/sda1` - 1 GB (EFI Boot) - montado en `/boot/efi`
  - `/dev/sda2` - 446.1 GB (Sistema) - montado en `/`

#### Disco Secundario - HDD 🔄
- **Dispositivo:** /dev/sdc (931.5 GB total)
- **Tipo:** **HDD** (ROTA=1 - disco rotacional)
- **Modelo:** TOSHIBA MQ01ABD100 (1TB, 2.5")
- **Particiones:**
  - `/dev/sdc1` - 200 MB
  - `/dev/sdc2` - 931.3 GB

#### Uso de Disco
- **Filesystem raíz:** /dev/sda2
- **Tamaño:** 439 GB
- **Usado:** 227 GB (55%)
- **Disponible:** 189 GB

### Estado del Sistema
- **Uptime:** 8 días, 23 horas, 10 minutos
- **Load Average:** 1.43, 0.95, 0.76
- **Usuarios conectados:** 6
- **Estado:** ⚠️ Requiere reinicio del sistema (actualizaciones pendientes)

### Dispositivos Adicionales
- **Snaps instalados:** Firefox, Thunderbird, Simplenote, Gnome, firmware-updater, etc.
- **Usuario SSH:** hector

### Actualizaciones Pendientes
- ⚠️ 4 actualizaciones disponibles
- ⚠️ **Reinicio del sistema requerido**

### Notas Especiales
- 💻 Hardware: **Mac mini (modelo 2012, 6,1)**
- 🔌 Disco secundario de 931.5 GB disponible
- ⏱️ Sistema estable (8+ días de uptime)
- 🏠 Conexión local directa (192.168.1.23)

---

## 4. INSPIRON13 (100.65.52.49 / 100.120.133.19) ✅

**Estado de conexión:** 
- Windows: 100.65.52.49 (Activa)
- WSL2: 100.120.133.19 (Activa)

### Información del Hardware
- **Fabricante:** Dell Inc.
- **Modelo:** Inspiron 5301 (13")
- **Serie:** Inspiron
- **SKU:** 09FB
- **Serial Number:** 96VLG63
- **BIOS:** Dell Inc. v2 (22/11/2024)
- **Año:** ~2020-2021 (11va generación Intel)

### Sistema Operativo

#### Windows 11 (Host Principal)
- **SO:** Microsoft Windows 11 Home
- **Versión:** 10.0.26200
- **Build:** 26200
- **Windows Version:** 2009
- **Arquitectura:** 64 bits

#### WSL2 (Linux Subsystem)
- **Distribución:** Ubuntu 24.04.1 LTS (Noble Numbat)
- **Kernel:** 6.6.87.2-microsoft-standard-WSL2
- **Hostname WSL:** DESKTOP-PDHNG2P
- **Arquitectura:** x86_64
- **Usuario SSH:** hsanchezp

### CPU
- **Modelo:** Intel(R) Core(TM) i5-1135G7 @ 2.40GHz
- **Generación:** 11th Gen Intel (Tiger Lake)
- **Núcleos Físicos:** 4 cores
- **Núcleos Lógicos:** 8 threads (Hyper-Threading)
- **Procesadores:** 1 socket
- **NUMA:** node0 (CPUs 0-7)

### Memoria RAM (Física - Windows)
- **Total Instalada:** 8 GB (7.73 GiB)
- **Tipo:** DDR4
- **Velocidad:** 4267 MT/s
- **Velocidad Configurada:** 4267 MT/s
- **Arquitectura:** Dual Channel

#### Configuración de Módulos
- **Slot 1 (Motherboard):**
  - 4 GB DDR4-4267
  - Part Number: HCNNNBKMBLHR-NEE
  - Soldado a la placa madre

- **Slot 2 (Motherboard):**
  - 4 GB DDR4-4267
  - Part Number: HCNNNBKMBLHR-NEE
  - Soldado a la placa madre

**⚠️ Nota:** La RAM está soldada a la placa madre (no upgradeable)

#### Asignación WSL2
- **RAM asignada a WSL:** 3.7 GiB (dinámica)
- **Disponible en WSL:** 3.0 GiB
- **Swap WSL:** 1.0 GiB

### GPU
- **Modelo:** Intel(R) Iris(R) Xe Graphics
- **Familia:** Intel Iris Xe Graphics Family
- **VRAM:** 128 MB dedicados (compartida con RAM del sistema)
- **Driver:** 31.0.101.5333
- **Tipo:** Gráficos integrados

### Almacenamiento

#### Disco Principal (NVMe SSD) ✨
- **Modelo:** NVMe PC SN530 NVMe WDC 256GB
- **Tipo:** SSD NVMe
- **Bus:** RAID (controlador NVMe)
- **Capacidad Total:** 256 GB (238 GiB)
- **Estado:** Healthy ✅
- **Estado Operacional:** OK
- **Fabricante:** Western Digital

#### Particiones Windows
- Unidad C: Sistema Windows principal
- Disponible via WSL en: `/mnt/c`

#### Disco Virtual WSL
- **Dispositivo WSL:** /dev/sdd (1TB VHDX)
- **Usado:** 1.6 GB (1%)
- **Disponible:** 955 GB
- **Filesystem:** ext4

### Estado del Sistema
- **Uptime Windows:** Variable
- **Uptime WSL:** 42 minutos (al momento de captura)
- **Load Average (WSL):** 0.06, 0.07, 0.09
- **Usuarios conectados (WSL):** 4

### Software Instalado
- **Docker Desktop:** ✅ Instalado y funcionando
- **WSL2:** ✅ Habilitado
- **WSLg:** ✅ Habilitado (soporte gráfico Linux)
- **Tailscale:** ✅ En Windows y WSL

### Notas Especiales
- 💻 **Laptop Dell Inspiron 13 5301** ultraportátil
- 🚀 CPU de **11va generación** (la más moderna de la red)
- 🐧 **Dual boot virtual**: Windows 11 + WSL2 Ubuntu
- 🐳 Docker Desktop integrado con WSL2
- 🖥️ WSLg para aplicaciones gráficas Linux
- 📁 Acceso bidireccional entre filesystems
- ⚡ **SSD NVMe** de alta velocidad
- 🎨 **Intel Iris Xe** - GPU integrada moderna
- ⚠️ **RAM soldada** - No expandible más allá de 8GB
- 🔗 **Doble presencia en Tailscale** (Windows + WSL)

---

## 5. INSPIRON15 (100.97.3.35 / 100.96.32.5) ✅

**Estado de conexión:** 
- Windows: 100.97.3.35 (Activa)
- WSL2: 100.96.32.5 (Offline hace 15h)

### Información del Hardware
- **Fabricante:** Dell Inc.
- **Modelo:** Inspiron 3593 (15")
- **Serie:** Inspiron
- **SKU:** 0979
- **Serial Number:** C2C1S53
- **BIOS:** Dell Inc. v20170001 (06/03/2024)
- **Año:** ~2019-2020 (10ma generación Intel)
- **Hostname:** LaptopGrande
- **Usuario SSH:** hecto

### Sistema Operativo

#### Windows 11 (Host Principal)
- **SO:** Microsoft Windows 11 Home Single Language
- **Versión:** 10.0.26200
- **Build:** 26200
- **Windows Version:** 2009
- **Arquitectura:** 64 bits

### CPU
- **Modelo:** Intel(R) Core(TM) i7-1065G7 @ 1.30GHz
- **Generación:** 10th Gen Intel (Ice Lake)
- **Núcleos Físicos:** 4 cores
- **Núcleos Lógicos:** 8 threads (Hyper-Threading)
- **Procesadores:** 1 socket

### Memoria RAM (Física - Windows)
- **Total Instalada:** 8 GB (7.77 GiB)
- **Tipo:** DDR4 SODIMM
- **Velocidad:** 2667 MT/s
- **Velocidad Configurada:** 2667 MT/s
- **Fabricante:** Samsung
- **Part Number:** M471A1K43CB1-CTD
- **Form Factor:** SO-DIMM (260-pin, Form Factor 12)

#### Configuración de Módulos
- **Slot DIMM A:**
  - 8 GB DDR4-2667
  - Samsung M471A1K43CB1-CTD
  - SO-DIMM removible

**⚠️ Nota:** Solo 1 slot ocupado - **Upgradeable a 16GB o más** (agregar otro módulo)

#### Capacidad de Upgrade 🔧
- **Slots totales:** Probablemente 2 slots SO-DIMM
- **Slots ocupados:** 1 (DIMM A con 8GB)
- **Slots libres:** 1 disponible
- **Upgrade sugerido:** Agregar 8GB o 16GB adicionales

### GPU (Dual Graphics) ⚡

#### GPU Integrada
- **Modelo:** Intel(R) Iris(R) Plus Graphics
- **VRAM:** 1 GB dedicados
- **Driver:** 31.0.101.2127
- **Familia:** Intel Iris Graphics Family

#### GPU Dedicada 🎮
- **Modelo:** NVIDIA GeForce MX230
- **VRAM:** 2 GB GDDR5
- **Driver:** 32.0.15.5612
- **Tipo:** GPU dedicada

#### Dispositivos Adicionales
- **DisplayLink USB Device** (x2) - Adaptadores de video USB externos

### Almacenamiento

#### Disco Interno (NVMe SSD) ✨
- **Modelo:** ADATA IM2P33F3 NVMe 256GB
- **Tipo:** SSD NVMe
- **Bus:** RAID (controlador NVMe)
- **Capacidad Total:** 256 GB (238 GiB)
- **Estado:** Healthy ✅
- **Fabricante:** ADATA

#### Disco Externo USB 🔌
- **Modelo:** TOSHIBA EXTERNAL_USB
- **Tipo:** USB Storage
- **Bus:** USB
- **Capacidad Total:** 1 TB (931 GiB)
- **Estado:** Healthy ✅
- **Conexión:** USB externa

### Estado del Sistema
- **Conexión SSH:** Activa vía Tailscale
- **Windows:** Funcionando
- **WSL2:** Offline (15h)

### Notas Especiales
- 💻 **Laptop Dell Inspiron 15 3593** (15 pulgadas)
- 🎮 **GPU DEDICADA NVIDIA MX230** - La única máquina con GPU dedicada en la red
- 🚀 CPU **i7 de 10ma generación** (Ice Lake)
- 🔧 **RAM UPGRADEABLE** - Tiene 1 slot libre para expansión
- 💾 **SSD NVMe ADATA** de 256GB
- 💿 **Disco externo Toshiba 1TB** conectado por USB
- 🖥️ **Soporte multi-monitor** con DisplayLink USB
- 🐧 WSL2 disponible pero actualmente offline

---

## Instrucciones para Acceder a las Máquinas Remotas

### 🚀 Acceso Rápido SSH (Sin Contraseña)

Todas las máquinas están configuradas con autenticación SSH sin contraseña via Tailscale. Simplemente usa el nombre corto:

\`\`\`bash
# Acceso directo a cualquier máquina
ssh vostro
ssh cfocoder3
ssh macmini
ssh inspiron13
ssh inspiron15
\`\`\`

### Acceso Alternativo por IP

Si prefieres usar IPs o necesitas especificar usuario:

\`\`\`bash
ssh cfocoder@100.116.107.52    # vostro
ssh ubuntu@100.105.68.15       # cfocoder3
ssh hector@100.110.109.43      # macmini
ssh hecto@100.65.52.49         # inspiron13
ssh hecto@100.97.3.35          # inspiron15
\`\`\`

---

## Cluster de Ollama Distribuido 🤖

Todas las máquinas del cluster tienen Ollama instalado y pueden ser usadas para inferencia distribuida:

| Máquina | IP Tailscale | CPU | RAM | Ollama | Modelos Instalados | Endpoint |
|---------|--------------|-----|-----|--------|-------------------|----------|
| **vostro** | 100.116.107.52 | i5-7200U (2C/4T) | **32 GB** | ✅ | ministral-3:8b, ministral-3:3b, gemma3:1b | http://100.116.107.52:11434 |
| **cfocoder3** | 100.105.68.15 | ARM Neoverse-N1 (4C) | 24 GB | ✅ | gemma3:1b | http://100.105.68.15:11434 |
| **macmini** | 100.110.109.43 | i5-3210M (2C/4T) | 16 GB | ✅ | gemma3:1b | http://100.110.109.43:11434 |
| **inspiron13** | 100.65.52.49 | i5-1135G7 (4C/8T) | 8 GB | ✅ | gemma3:1b | http://100.65.52.49:11434 |
| **inspiron15** | 100.97.3.35 | **i7-1065G7 (4C/8T)** | 8 GB + **GPU MX230** | ✅ | gemma3:1b | http://100.97.3.35:11434 |

### Capacidad Total del Cluster
- **CPU Total:** 16 cores / 24 threads
- **RAM Total:** 88 GB
- **GPU Dedicada:** NVIDIA MX230 2GB (inspiron15) 🎮
- **Arquitecturas:** x86_64 (4 máquinas) + ARM (1 máquina)

### Estrategias de Uso Recomendadas

**1. Especialización por máquina:**
- `vostro` → Modelos grandes (8b) - **32GB RAM**
- `cfocoder3` → Procesamiento rápido (ARM 4 cores)
- `inspiron13` → CPU moderna (11va gen, 8 threads)
- `inspiron15` → **Aceleración GPU** (MX230) + i7
- `macmini` → Tareas ligeras / backup

**2. Load Balancing:**
```python
ollama_cluster = {
    'heavy': 'http://100.116.107.52:11434',    # vostro (32GB)
    'fast': 'http://100.105.68.15:11434',      # cfocoder3 (ARM)
    'gpu': 'http://100.97.3.35:11434',         # inspiron15 (GPU)
    'modern': 'http://100.65.52.49:11434',     # inspiron13 (11va gen)
}
```

**3. Procesamiento Paralelo con Dask:**
- Distribuir lotes de documentos entre nodos
- Cada nodo procesa independientemente
- Agregar resultados con Dask
- Aprovechar 16 cores totales simultáneamente

### Notas de Rendimiento
- ⚠️ **Velocidad actual vostro:** 2.76 tokens/s con ministral-3:8b (CPU bottleneck)
- ✅ **Solución:** Distribuir carga entre 5 nodos = ~10-15 tokens/s efectivos
- 🎯 **Mejor opción:** Usar inspiron15 con GPU para inferencia más rápida
- 💡 **RAM disponible:** vostro tiene 17GB libres para modelos grandes

---

## Notas Adicionales

- Todas las máquinas Linux están activas y accesibles vía Tailscale.
- La conexión directa indica que las máquinas están en la misma red local o tienen conectividad peer-to-peer óptima.
- Se detectó un problema de DNS en vostro que podría afectar la conectividad a Internet.
- **Cluster Dask + Ollama:** Las 5 máquinas forman un cluster híbrido para procesamiento distribuido y LLMs
- Red limpia y optimizada - dispositivos no utilizados removidos

---

## Próximos Pasos

1. ✅ Información de **vostro** recopilada y actualizada (RAM upgraded a 32GB)
2. ✅ Información de **cfocoder3** recopilada
3. ✅ Información de **macmini** recopilada
4. ✅ Información de **inspiron13** recopilada
5. ✅ Información de **inspiron15** recopilada
6. ✅ Documento completo actualizado

---

## Resumen Comparativo

| Especificación | VOSTRO | CFOCODER3 | MACMINI | INSPIRON13 | INSPIRON15 |
|----------------|--------|-----------|---------|------------|------------|
| **Arquitectura** | x86_64 (Intel) | aarch64 (ARM) | x86_64 (Intel) | x86_64 (Intel) | x86_64 (Intel) |
| **CPU** | i5-7200U (7ma) | ARM Neoverse-N1 | i5-3210M (3ra) | i5-1135G7 (11va) | **i7-1065G7 (10ma)** |
| **Cores/Threads** | 2C/4T | 4C/4T | 2C/4T | 4C/8T | 4C/8T |
| **RAM Total** | **32 GB** ✨ | 24 GB | 16 GB | 8 GB | 8 GB |
| **RAM Tipo** | DDR4-3200 | Virtual ECC | DDR3-1333 | DDR4-4267 (soldada) | DDR4-2667 (SO-DIMM) |
| **RAM Upgradeable** | ✅ Máx. alcanzado | Cloud config | ❌ Al máximo | ❌ Soldada | **✅ 1 slot libre** |
| **RAM Disponible** | **24 GiB** ⚡ | 15 GiB | 8.2 GiB | ~5-6 GiB | ~6 GiB |
| **Disco Principal** | 915 GB SSD | 45 GB Block | 439 GB SSD | 256 GB NVMe | 256 GB NVMe |
| **Disco Secundario** | - | 151 GB Block | 931 GB HDD | - | **1 TB USB** |
| **GPU Integrada** | Intel HD 620 | N/A | Intel 3rd Gen | Intel Iris Xe | Intel Iris Plus |
| **GPU Dedicada** | No | No | No | No | **NVIDIA MX230 2GB** 🎮 |
| **Modelo** | Vostro 14-3468 | VM A1.Flex | Mac mini 6,1 | Inspiron 5301 | Inspiron 3593 |
| **Pantalla** | 14" | N/A | Desktop | 13" | **15"** |
| **Año** | ~2017 | Cloud | 2012 | ~2020-2021 | ~2019-2020 |
| **SO** | Ubuntu 24.04 | Ubuntu 24.04 | Ubuntu 24.04 | Win 11 + WSL2 | Win 11 + WSL2 |
| **Tipo** | Laptop | Cloud | Desktop | Ultraportátil | Laptop estándar |

### Observaciones Importantes

#### 🏆 Rendimiento
- **Mayor RAM:** vostro (32 GB) ✨ **UPGRADED!** - Ideal para cargas pesadas y Docling
- **Segunda mayor RAM:** cfocoder3 (24 GB) - Cloud worker
- **Más estable:** macmini (8+ días uptime)
- **CPU más reciente:** inspiron13 (Intel 11va generación, Tiger Lake)
- **CPU i7:** inspiron15 (único con procesador i7, 10ma generación)
- **Más threads:** inspiron13 e inspiron15 (8 threads cada uno) - Mejor para multitarea
- **CPU más antigua:** macmini (Intel 3ra generación - 2012)
- **RAM más rápida:** inspiron13 (DDR4-4267 MHz)
- **GPU dedicada:** inspiron15 (NVIDIA GeForce MX230 2GB) 🎮 **ÚNICA CON GPU DEDICADA**
- **GPU integrada más moderna:** inspiron13 (Intel Iris Xe)
- **Mayor RAM disponible:** vostro (24 GiB libres) - **Perfecta para Docling/Dask**

#### 💾 Almacenamiento
- **Mayor capacidad total:** vostro (915 GB SSD disponibles)
- **Más espacio libre:** vostro (445 GB libres)
- **Discos más rápidos:** inspiron13 e inspiron15 (ambos con NVMe PCIe)
- **Discos SSD:** vostro, macmini, inspiron13, inspiron15 (todos con SSD/NVMe)
- **Disco HDD tradicional:** macmini tiene un HDD Toshiba 1TB adicional
- **Cloud Storage:** cfocoder3 usa Block Volumes de Oracle (NVMe backend)
- **Disco adicional:** 
  - cfocoder3: 151 GB Block Volume montado en `/mnt/myvolume`
  - macmini: 931 GB HDD Toshiba sin montar
  - inspiron13: 1TB VHDX para WSL (muy poco usado)
  - inspiron15: **1TB USB externo Toshiba** (almacenamiento móvil)

#### ⚡ Recursos
- **Mejor balance RAM/CPU:** cfocoder3 (4 cores ARM + 23 GB RAM)
- **RAM upgradeable:** inspiron15 (1 slot libre SO-DIMM DDR4) - **Puede expandir a 16GB o más**
- **Pantalla más grande:** inspiron15 (15 pulgadas)
- **Uso de swap:** Solo macmini usa swap activamente (2.2 GB)
- **Virtualización:** macmini tiene VT-x habilitado

#### 🎮 Gaming y Multimedia
- **GPU dedicada:** inspiron15 (NVIDIA MX230 2GB) - Única con capacidades gráficas dedicadas
- **Intel Iris Plus:** inspiron15 (GPU integrada) + NVIDIA MX230 = gráficos híbridos
- **Ideal para:** Edición de video ligera, juegos casuales, aceleración CUDA

#### 🔧 Mantenimiento
- **Actualizaciones pendientes:** macmini (4 actualizaciones + reinicio requerido)
- **Problema DNS:** vostro (aviso de Tailscale)

#### 🌐 Ubicación
- **Cloud:** cfocoder3 (Oracle Cloud Infrastructure - VM.Standard.A1.Flex)
- **Local Linux:** vostro y macmini (red 177.249.174.222)
- **Windows 11:** inspiron13 e inspiron15 (ambos con WSL2 Ubuntu)
- **Red local:** macmini visible en 192.168.1.23

#### 🏭 Hardware
- **Más reciente:** inspiron13 (Dell Inspiron 13 5301, ~2020-2021, 11va gen)
- **Segundo más reciente:** vostro (Dell Vostro 14-3468, ~2017, 7ma gen)
- **Más antiguo:** macmini (Apple Mac mini 6,1, Late 2012, 3ra gen)
- **Virtualizado:** cfocoder3 (KVM en Oracle Cloud)
- **Disco más rápido:** inspiron13 con NVMe SSD (WDC PC SN530)
- **Discos SATA SSD:** vostro (WDC 1TB) y macmini (WD Green 480GB)
- **Almacenamiento empresarial:** cfocoder3 con Block Volumes de Oracle (NVMe)
- **RAM soldada (no upgradeable):** inspiron13 (8GB máximo)
- **RAM upgradeable:** vostro (hasta 32GB) y macmini (ya al máximo 16GB)

#### 💡 Casos de Uso Recomendados
- **vostro:** ⭐ **Worker PRINCIPAL para Docling/Dask** - 32GB RAM, desarrollo Linux nativo, máximo almacenamiento
- **cfocoder3:** Servicios cloud 24/7, arquitectura ARM, alta disponibilidad
- **inspiron13:** Desarrollo Windows/Linux híbrido, Docker, máximo rendimiento CPU/GPU, ultraportátil
- **macmini:** Servidor local estable, almacenamiento masivo (1TB HDD adicional), bajo consumo

#### ⚠️ Limitaciones
- **inspiron13:** RAM soldada (8GB no ampliable), almacenamiento limitado (256GB)
- **vostro:** GPU integrada básica (HD 620), pero ahora con **32GB RAM** ✅
- **macmini:** Hardware antiguo (2012), CPU lenta para tareas modernas
- **cfocoder3:** Almacenamiento limitado (45GB sistema + 151GB volumen), limitado por Always Free Tier
