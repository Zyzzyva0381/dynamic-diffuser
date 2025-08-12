#!/usr/bin/env python3
"""
ESP32 磁铁控制器 Python 接口
协议格式：[0xAA][0x55][磁铁ID+0x0A][动作+0x0A]
- 磁铁ID: 0-8 (发送时加上0x0A，即0x0A-0x13)
- 动作: 0=收缩(IN), 1=伸展(OUT) (发送时加上0x0A，即0x0A, 0x0B)
"""

import serial
import time
import sys
from typing import Optional


class MagnetController:
    """ESP32磁铁控制器类"""
    
    # 协议常量
    HEADER1 = 0xAA
    HEADER2 = 0x55
    OFFSET = 0x0A  # 偏移量，避免常用数字冲突
    
    # 动作定义
    ACTION_IN = 0   # 收缩
    ACTION_OUT = 1  # 伸展
    
    def __init__(self, port: str = 'COM5', baudrate: int = 115200, timeout: float = 1.0):
        """
        初始化磁铁控制器
        
        Args:
            port: 串口端口名 (如 'COM3' 或 '/dev/ttyUSB0')
            baudrate: 波特率，默认115200
            timeout: 串口超时时间，默认1.0秒
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn: Optional[serial.Serial] = None
        self.is_connected = False
        
    def connect(self) -> bool:
        """
        连接到ESP32设备
        
        Returns:
            bool: 连接是否成功
        """
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            time.sleep(2)  # 等待ESP32重启完成
            self.is_connected = True
            print(f"已成功连接到 {self.port}")
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.is_connected = False
            print("已断开连接")
    
    def _send_command(self, magnet_id: int, action: int) -> bool:
        """
        发送命令到ESP32
        
        Args:
            magnet_id: 磁铁ID (0-8)
            action: 动作 (0=收缩, 1=伸展)
            
        Returns:
            bool: 发送是否成功
        """
        if not self.is_connected or not self.serial_conn:
            print("错误: 设备未连接")
            return False
        
        # 验证参数
        if not (0 <= magnet_id <= 8):
            print(f"错误: 无效的磁铁ID {magnet_id}，应该在0-8之间")
            return False
        
        if action not in [self.ACTION_IN, self.ACTION_OUT]:
            print(f"错误: 无效的动作 {action}")
            return False
        
        try:
            # 构建命令
            command = bytes([
                self.HEADER1,                    # 0xAA
                self.HEADER2,                    # 0x55  
                magnet_id + self.OFFSET,         # 磁铁ID + 0x0A
                action + self.OFFSET             # 动作 + 0x0A
            ])
            
            # 发送命令
            self.serial_conn.write(command)
            self.serial_conn.flush()
            
            print(f"发送命令: 磁铁{magnet_id} {'收缩' if action == self.ACTION_IN else '伸展'}")
            print(f"原始字节: {' '.join(f'0x{b:02X}' for b in command)}")
            
            return True
        except Exception as e:
            print(f"发送命令失败: {e}")
            return False
    
    def magnet_in(self, magnet_id: int) -> bool:
        """
        让指定磁铁收缩
        
        Args:
            magnet_id: 磁铁ID (0-8)
            
        Returns:
            bool: 操作是否成功
        """
        return self._send_command(magnet_id, self.ACTION_IN)
    
    def magnet_out(self, magnet_id: int) -> bool:
        """
        让指定磁铁伸展
        
        Args:
            magnet_id: 磁铁ID (0-8)
            
        Returns:
            bool: 操作是否成功
        """
        return self._send_command(magnet_id, self.ACTION_OUT)
    
    def control_magnet(self, magnet_id: int, action: str) -> bool:
        """
        控制磁铁 (字符串接口)
        
        Args:
            magnet_id: 磁铁ID (0-8)
            action: 动作字符串 ("in"/"IN" 或 "out"/"OUT")
            
        Returns:
            bool: 操作是否成功
        """
        action_lower = action.lower()
        if action_lower == "in":
            return self.magnet_in(magnet_id)
        elif action_lower == "out":
            return self.magnet_out(magnet_id)
        else:
            print(f"错误: 无效的动作 '{action}'，应该是 'in' 或 'out'")
            return False
    
    def test_all_magnets(self, delay: float = 2.0):
        """
        测试所有磁铁
        
        Args:
            delay: 每个动作之间的延时（秒）
        """
        print("开始测试所有磁铁...")
        for i in range(9):
            print(f"测试磁铁 {i}")
            
            # 伸展
            self.magnet_out(i)
            time.sleep(delay)
            
            # 收缩
            self.magnet_in(i)
            time.sleep(delay)
        
        print("所有磁铁测试完成")
    
    def read_response(self, timeout: float = 1.0) -> str:
        """
        读取ESP32的响应信息
        
        Args:
            timeout: 读取超时时间
            
        Returns:
            str: 接收到的字符串
        """
        if not self.is_connected or not self.serial_conn:
            return ""
        
        start_time = time.time()
        response = ""
        
        while time.time() - start_time < timeout:
            if self.serial_conn.in_waiting > 0:
                try:
                    data = self.serial_conn.readline().decode('utf-8').strip()
                    if data:
                        response += data + "\n"
                except:
                    break
            else:
                time.sleep(0.01)
        
        return response.strip()


def main():
    """示例用法"""
    if len(sys.argv) < 2:
        print("用法: python commander.py <串口端口>")
        print("例如: python commander.py COM3")
        print("或者: python commander.py /dev/ttyUSB0")
        return
    
    port = sys.argv[1]
    controller = MagnetController(port)
    
    # 连接设备
    if not controller.connect():
        return
    
    try:
        # 简单的交互式控制
        print("\n磁铁控制器已就绪!")
        print("命令格式: <磁铁ID> <动作>")
        print("磁铁ID: 0-8")
        print("动作: in 或 out")
        print("特殊命令: test (测试所有磁铁), quit (退出)")
        print("例如: 0 in, 3 out, test")
        
        while True:
            cmd = input("\n请输入命令: ").strip()
            
            if cmd.lower() == 'quit':
                break
            elif cmd.lower() == 'test':
                controller.test_all_magnets()
            else:
                parts = cmd.split()
                if len(parts) == 2:
                    try:
                        magnet_id = int(parts[0])
                        action = parts[1]
                        controller.control_magnet(magnet_id, action)
                        
                        # 读取可能的响应
                        response = controller.read_response(0.5)
                        if response:
                            print(f"设备响应: {response}")
                            
                    except ValueError:
                        print("错误: 磁铁ID必须是数字")
                else:
                    print("错误: 命令格式不正确")
    
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    finally:
        controller.disconnect()


if __name__ == "__main__":
    main()
