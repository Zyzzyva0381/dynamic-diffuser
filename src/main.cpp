/*
 * ESP32 - 串口控制电磁铁系统
 * 功能：
 * 1. 通过串口接收三个字节的命令来控制9个电磁铁
 * 2. 第一个字节：标识符(0xAA)
 * 3. 第二个字节：磁铁编号(0-8)
 * 4. 第三个字节：动作(0=收缩in, 1=伸展out)
 * 5. 每个磁铁使用两个GPIO引脚控制
 */

// (base) PS D:\programs\diffuser-hardware> python -m platformio run -t upload

#include <Arduino.h>

// 定义18个GPIO引脚编号，每两个控制一个电磁铁
const int outputPinsCount = 18;
const int magnetCount = 9; // 9个电磁铁
int outputPins[outputPinsCount] = {
  4, 5, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33, 2
};

// 协议定义 - 使用4字节协议提高安全性
const uint8_t COMMAND_HEADER1 = 0xAA; // 第一个命令标识符
const uint8_t COMMAND_HEADER2 = 0x55; // 第二个命令标识符  
const int COMMAND_LENGTH = 4; // 命令长度：标识符1 + 标识符2 + 磁铁ID + 动作

// 串口命令缓冲区
uint8_t commandBuffer[COMMAND_LENGTH];
int bufferIndex = 0;
unsigned long lastByteTime = 0; // 记录最后一次接收字节的时间
const unsigned long TIMEOUT_MS = 100; // 超时时间100ms

// 调试模式控制
bool debugMode = false; // 设置为false可减少输出信息

void setup() {
  // 启动串口通信
  Serial.begin(115200);
  Serial.println("ESP32 Magnet Control System Started");
  Serial.println("Command Format: [0xAA][0x55][Magnet_ID+0x0A][Action+0x0A]");
  Serial.println("Example: Magnet 0 IN = 0xAA 0x55 0x0A 0x0A");
  Serial.println("Example: Magnet 0 OUT = 0xAA 0x55 0x0A 0x0B");
  Serial.print("Debug Mode: ");
  Serial.println(debugMode ? "ON" : "OFF");

  // 将所有引脚设置为输出模式
  for (int i = 0; i < outputPinsCount; i++) {
    int pin = outputPins[i];
    pinMode(pin, OUTPUT);
    digitalWrite(pin, LOW); // 初始状态设为LOW
    if (debugMode) {
      Serial.print("Pin GPIO");
      Serial.print(pin);
      Serial.println(" initialized as OUTPUT.");
    }
  }

  Serial.println("Setup complete. Ready to receive commands...");
}

void controlMagnet(int magnetId, int action) {
  // 检查磁铁ID是否有效
  if (magnetId < 0 || magnetId >= magnetCount) {
    Serial.print("Error: Invalid magnet ID: ");
    Serial.println(magnetId);
    return;
  }

  // 计算对应的引脚索引
  int pinIndex1 = magnetId * 2;     // 第一个引脚（用于in）
  int pinIndex2 = magnetId * 2 + 1; // 第二个引脚（用于out）

  // 首先将两个引脚都设为LOW（停止状态）
  digitalWrite(outputPins[pinIndex1], LOW);
  digitalWrite(outputPins[pinIndex2], LOW);
  
  delay(10); // 短暂延时确保状态切换

  if (action == 0) {
    // 收缩 (in): 第一个引脚LOW，第二个引脚HIGH
    digitalWrite(outputPins[pinIndex1], LOW);
    digitalWrite(outputPins[pinIndex2], HIGH);
    if (debugMode) {
      Serial.print("Magnet ");
      Serial.print(magnetId);
      Serial.println(" -> IN (retracting)");
    }
  } else if (action == 1) {
    // 伸展 (out): 第一个引脚HIGH，第二个引脚LOW
    digitalWrite(outputPins[pinIndex1], HIGH);
    digitalWrite(outputPins[pinIndex2], LOW);
    if (debugMode) {
      Serial.print("Magnet ");
      Serial.print(magnetId);
      Serial.println(" -> OUT (extending)");
    }
  } else {
    if (debugMode) {
      Serial.print("Error: Invalid action: ");
      Serial.println(action);
    }
    return;
  }

  // 动作持续时间
  delay(15);

  // 停止动作，将所有引脚设为LOW
  digitalWrite(outputPins[pinIndex1], LOW);
  digitalWrite(outputPins[pinIndex2], LOW);
  
  if (debugMode) {
    Serial.print("Magnet ");
    Serial.print(magnetId);
    Serial.println(" -> STOP");
  }
}

void processCommand() {
  // 验证双重命令标识符
  if (commandBuffer[0] != COMMAND_HEADER1 || commandBuffer[1] != COMMAND_HEADER2) {
    if (debugMode) {
      Serial.print("Error: Invalid command headers: 0x");
      Serial.print(commandBuffer[0], HEX);
      Serial.print(" 0x");
      Serial.println(commandBuffer[1], HEX);
    }
    return;
  }
  
  // 从接收到的字节中减去0x0A来得到实际的磁铁ID和动作
  int magnetId = commandBuffer[2] - 0x0A;
  int action = commandBuffer[3] - 0x0A;
  
  // 更严格的参数验证
  if (magnetId < 0 || magnetId >= magnetCount) {
    if (debugMode) {
      Serial.print("Error: Invalid magnet ID in command: ");
      Serial.print(magnetId);
      Serial.print(" (raw byte: 0x");
      Serial.print(commandBuffer[2], HEX);
      Serial.println(")");
    }
    return;
  }
  
  if (action != 0 && action != 1) {
    if (debugMode) {
      Serial.print("Error: Invalid action in command: ");
      Serial.print(action);
      Serial.print(" (raw byte: 0x");
      Serial.print(commandBuffer[3], HEX);
      Serial.println(")");
    }
    return;
  }
  
  if (debugMode) {
    Serial.print("Received valid command: Magnet=");
    Serial.print(magnetId);
    Serial.print(", Action=");
    Serial.println(action);
  }
  
  controlMagnet(magnetId, action);
}

void loop() {
  unsigned long currentTime = millis();
  
  // 检查是否超时，如果超时则重置缓冲区
  if (bufferIndex > 0 && (currentTime - lastByteTime) > TIMEOUT_MS) {
    if (debugMode) {
      Serial.println("Command timeout, resetting buffer");
    }
    bufferIndex = 0;
  }
  
  // 检查串口是否有数据可读
  if (Serial.available() > 0) {
    uint8_t receivedByte = Serial.read();
    lastByteTime = currentTime;
    
    // 状态机处理命令接收
    if (bufferIndex == 0) {
      // 等待第一个标识符
      if (receivedByte == COMMAND_HEADER1) {
        commandBuffer[bufferIndex] = receivedByte;
        bufferIndex++;
      } else {
        // 静默忽略无效的第一个字节
      }
    } else if (bufferIndex == 1) {
      // 验证第二个标识符
      if (receivedByte == COMMAND_HEADER2) {
        commandBuffer[bufferIndex] = receivedByte;
        bufferIndex++;
      } else {
        // 如果第二个字节不匹配，重置并检查是否是新的第一个标识符
        if (receivedByte == COMMAND_HEADER1) {
          commandBuffer[0] = receivedByte;
          bufferIndex = 1;
        } else {
          bufferIndex = 0;
        }
      }
    } else {
      // 接收剩余的命令字节
      commandBuffer[bufferIndex] = receivedByte;
      bufferIndex++;
    }
    
    // 当接收到完整命令后处理
    if (bufferIndex >= COMMAND_LENGTH) {
      processCommand();
      bufferIndex = 0; // 重置缓冲区索引
    }
  }
  
  // 短暂延时避免过度占用CPU
  delay(1);
}
