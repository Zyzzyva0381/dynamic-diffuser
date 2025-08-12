#!/usr/bin/env python3
"""
磁铁控制器使用示例
"""

from commander import MagnetController
import time

def example_usage():
    """基本使用示例"""
    # 创建控制器实例 (请根据你的实际串口修改)
    controller = MagnetController("COM3")  # Windows
    # controller = MagnetController("/dev/ttyUSB0")  # Linux
    
    # 连接设备
    if controller.connect():
        try:
            # 示例1: 控制单个磁铁
            print("示例1: 控制磁铁0")
            controller.magnet_out(0)  # 磁铁0伸展
            time.sleep(1)
            controller.magnet_in(0)   # 磁铁0收缩
            time.sleep(1)
            
            # 示例2: 使用字符串接口
            print("示例2: 使用字符串接口控制磁铁1")
            controller.control_magnet(1, "out")
            time.sleep(1)
            controller.control_magnet(1, "in")
            time.sleep(1)
            
            # 示例3: 顺序控制多个磁铁
            print("示例3: 顺序控制磁铁0-2")
            for i in range(3):
                print(f"控制磁铁 {i}")
                controller.magnet_out(i)
                time.sleep(0.5)
                controller.magnet_in(i)
                time.sleep(0.5)
            
            # 示例4: 测试所有磁铁 (可选)
            # print("示例4: 测试所有磁铁")
            # controller.test_all_magnets(delay=1.0)
            
        finally:
            # 确保断开连接
            controller.disconnect()
    else:
        print("无法连接到设备")

def pattern_demo():
    """演示一个简单的磁铁模式"""
    controller = MagnetController("COM3")  # 请修改为你的串口
    
    if controller.connect():
        try:
            print("演示波浪模式...")
            
            # 波浪效果：依次伸展，然后依次收缩
            for i in range(9):
                controller.magnet_out(i)
                time.sleep(0.3)
            
            time.sleep(1)
            
            for i in range(9):
                controller.magnet_in(i)
                time.sleep(0.3)
                
        finally:
            controller.disconnect()

if __name__ == "__main__":
    print("磁铁控制器示例")
    print("1. 基本使用示例")
    print("2. 波浪模式演示")
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == "1":
        example_usage()
    elif choice == "2":
        pattern_demo()
    else:
        print("无效选择")
