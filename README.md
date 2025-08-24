# Dynamic Diffuser Project

## 项目简介
Dynamic Diffuser 是一个结合硬件和软件的项目，旨在通过单片机和上位机的协作实现动态扩散体的控制和优化。项目分为两个主要部分：

1. **单片机程序**：位于 `platformio.ini` 和 `src/` 目录下，用于控制硬件设备。
2. **上位机程序**：位于 `software/` 目录下，用于运行算法、数据处理和与硬件通信。

## 项目结构

```
platformio.ini
audio/
software/
src/
    main.cpp
```

### 主要目录说明

- **`platformio.ini` 和 `src/`**
  - 用于单片机程序的开发和烧录。
  - `platformio.ini` 是 PlatformIO 的配置文件，定义了硬件平台、框架和依赖。
  - `src/main.cpp` 是单片机程序的主入口，包含硬件逻辑的实现。

- **`software/`**
  - 包含上位机程序，用于运行强化学习算法、数据处理和与硬件通信。
  - 主要文件：
    - `commander.py`：用于与硬件通信的命令模块。
    - `diffuser_env.py`：定义了强化学习的环境。
    - `train_simple.py`：用于训练强化学习模型。
    - `evaluate.py`：评估训练好的模型。
    - `model.py`：定义了强化学习模型的结构。
    - `read_ni_device.py`：用于读取 NI 设备的数据。

- **`audio/`**
  - 包含音频生成相关的脚本和数据文件。

## 项目功能

1. **硬件控制**
   - 使用单片机程序控制动态扩散器的硬件行为。
   - 通过 PlatformIO 工具进行开发和烧录。

2. **强化学习算法**
   - 使用 DQN（深度 Q 网络）算法优化动态扩散器的性能。
   - 提供训练、评估和比较不同策略的功能。

3. **数据处理与通信**
   - 上位机程序与硬件设备通信，采集数据并进行处理。
   - 支持读取 NI 设备的数据。

## 使用说明

### 环境配置

#### 单片机部分
1. 安装 [PlatformIO](https://platformio.org/)。
2. 打开项目根目录，确保 `platformio.ini` 文件存在。
3. 使用以下命令编译和烧录程序：
   ```bash
   pio run --target upload
   ```

#### 上位机部分
1. 安装 Python 3.11（建议使用 `pythonversion.txt` 中的版本）。
2. 安装依赖：
   ```bash
   pip install -r software/requirements.txt
   ```
   **注意**：`requirements.txt` 中不包含 PlatformIO（`pio`），如需使用，请单独安装。

### 运行步骤

#### 单片机程序
1. 确保硬件连接正确。
2. 使用 PlatformIO 烧录程序到单片机。
3. 启动硬件设备。

#### 上位机程序
1. 运行 `train_simple.py` 以训练强化学习模型：
   ```bash
   python train_simple.py
   ```
2. 运行 `evaluate.py` 评估模型：
   ```bash
   python evaluate.py
   ```
3. 直接运行 `commander.py` 可以与硬件测试通信：
   ```bash
   python commander.py
   ```

### 日志与结果
- 训练日志存储在 `software/dqn_logs/` 目录下。
- 模型文件存储为 `software/dqn_diffuser_model.pth`。

## 注意事项
1. 确保硬件设备连接正确，避免通信失败。
2. 在运行上位机程序前，确保 Python 环境配置正确。
3. 如果需要修改单片机程序，请参考 `src/main.cpp`。

## 贡献与维护
- 有关问题，请联系项目所有者：Windy
