import torch
import numpy as np
import time
import matplotlib.pyplot as plt
from diffuser_env import DiffuserEnv
from model import DQNAgent

# --- 配置参数 ---
MODEL_PATH = "dqn_diffuser_model.pth"  # 指向您训练好的模型
PORT = 'COM5'                         # 确保串口号正确
NUM_STEPS = 500                       # 想要运行的总决策步数

# --- 初始化绘图 ---
plt.ion()  # 开启交互模式
fig, ax = plt.subplots()
reward_history = []
steps_history = []
line, = ax.plot(steps_history, reward_history, 'r-') # 返回一个包含一个元素的元组

# 设置图表标题和坐标轴标签
ax.set_title("Real-time Reward")
ax.set_xlabel("Step")
ax.set_ylabel("Reward")
ax.grid(True)

# --- 加载模型和环境 ---
print("正在加载环境和模型...")
env = DiffuserEnv(port=PORT)
state_dim = np.prod(env.observation_space.shape)
action_dim = env.action_space.n

# 加载模型
agent = DQNAgent(state_dim, action_dim)
try:
    agent.load(MODEL_PATH)
    agent.policy_net.eval()  # 设置为评估模式
    print(f"模型 {MODEL_PATH} 加载成功。")
except FileNotFoundError:
    print(f"错误：找不到模型文件 {MODEL_PATH}。请先运行 train_simple.py 进行训练。")
    env.close()
    exit()


# --- 评估循环 ---
print("开始进行实时决策和可视化...")
state, info = env.reset()
try:
    for step in range(NUM_STEPS):
        # 1. 获取动作掩码并选择最佳动作 (epsilon=0, 无探索)
        action_mask = info["action_mask"]
        action = agent.select_action(state, epsilon=0, action_mask=action_mask)
        
        # 2. 执行动作
        next_state, reward, terminated, truncated, info = env.step(action)
        print(f"Step {step+1}/{NUM_STEPS} | Action: {action}, Reward: {reward:.4f}")

        # 3. 更新状态
        state = next_state
        
        # 4. 更新并重绘图表
        reward_history.append(reward)
        steps_history.append(step)
        
        line.set_xdata(steps_history)
        line.set_ydata(reward_history)
        
        ax.relim()        # 重新计算坐标轴范围
        ax.autoscale_view() # 自动调整坐标轴
        
        fig.canvas.draw()   # 重绘图表
        fig.canvas.flush_events() # 处理GUI事件
        
        time.sleep(0.1) # 稍微暂停，以便能看清图表

        if terminated or truncated:
            print("Episode结束，正在重置环境...")
            state, info = env.reset()

except KeyboardInterrupt:
    print("\n评估被用户中断。")
finally:
    # --- 清理 ---
    print("正在关闭环境...")
    env.close()
    plt.ioff() # 关闭交互模式
    plt.show() # 显示最终的图表
    print("程序结束。")
