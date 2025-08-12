import gymnasium as gym
from gymnasium import spaces
import numpy as np
import time

# 导入您的项目模块
from read_ni_device import init_task as init_sensor, acquire_data, finalize as finalize_sensor
from commander import MagnetController

class DiffuserEnv(gym.Env):
    """
    用于电磁铁扩散器控制的自定义强化学习环境。

    Observation:
        - 类型: Box(10, 3)
        - 描述: 1秒内采集的10帧数据，每帧包含3个声道的响度（模值）。
        - 数据范围: [0, inf)

    Actions:
        - 类型: Discrete(19)
        - 描述: 18个动作对应9个电磁铁的伸/缩，1个动作用于“无操作”。
            - 0-8:   控制电磁铁 0-8 'IN' (收缩)
            - 9-17:  控制电磁铁 0-8 'OUT' (伸展)
            - 18:    'NO_OP' (无操作)

    Reward:
        - 奖励函数旨在最小化三个声道之间的响度差异。差异越小，奖励越高。
    """
    metadata = {'render_modes': ['human']}

    def __init__(self, port='COM5', sample_rate=12000, num_channels=3, com_port_ready_time=2.0):
        super(DiffuserEnv, self).__init__()

        # --- 初始化硬件接口 ---
        # 初始化电磁铁控制器
        self.controller = MagnetController(port=port)
        self.controller.connect()
        time.sleep(com_port_ready_time) # 等待串口稳定

        # 初始化NI数据采集设备
        self.sample_rate = sample_rate
        self.num_channels = num_channels
        self.sensor_duration_per_step = 1.0  # 每次step采集1秒数据
        self.num_frames = 10                 # 分成10帧
        self.samples_per_frame = int(self.sample_rate / self.num_frames)
        init_sensor(self.sample_rate, self.sensor_duration_per_step, self.num_channels)

        # --- 定义动作空间和观测空间 ---
        self.action_space = spaces.Discrete(19)  # 9个磁铁 * 2个动作 + 1个无操作
        self.observation_space = spaces.Box(low=0, high=np.inf, shape=(self.num_frames, self.num_channels), dtype=np.float32)

        # --- 内部状态 ---
        # 追踪9个电磁铁的当前状态 (0 for IN, 1 for OUT)
        self.magnet_states = np.zeros(9, dtype=int)
        self.current_step = 0
        self.max_steps = 1000 # 每轮episode的最大步数

    def _get_observation(self):
        """采集并处理传感器数据以形成观测值。"""
        raw_data = acquire_data(verbose=False) # (采样点数, 通道数)
        
        # 将数据分割成10帧并计算每帧的模（RMS）
        frames = np.array_split(raw_data, self.num_frames)
        observation = np.zeros((self.num_frames, self.num_channels), dtype=np.float32)

        for i, frame in enumerate(frames):
            # 计算每个声道的RMS值作为响度
            rms = np.sqrt(np.mean(frame**2, axis=0))
            observation[i, :] = rms
            
        return observation

    def _calculate_reward(self, observation):
        """根据观测值计算奖励。奖励的核心是最小化声道间的响度差异。"""
        # 计算每一帧内，三个声道响度的标准差
        # 标准差越小，说明声道间的响度差异越小
        std_devs = np.std(observation, axis=1)
        
        # 我们希望标准差越小越好，所以用其倒数作为奖励的一部分
        # 为避免除以零，加上一个很小的数epsilon
        reward = np.mean(1.0 / (std_devs + 1e-6))
        
        return float(reward)

    def step(self, action):
        """执行一个动作，获取新的状态和奖励。"""
        # 1. 执行动作
        self._take_action(action)

        # 2. 获取新的观测值
        observation = self._get_observation()

        # 3. 计算奖励
        reward = self._calculate_reward(observation)

        # 4. 判断是否结束
        self.current_step += 1
        terminated = False # 在这个任务中，通常不会有明确的“终止”状态
        truncated = self.current_step >= self.max_steps # 如果达到最大步数，则截断

        # 5. 获取信息（包括动作掩码）
        info = self._get_info()

        return observation, reward, terminated, truncated, info

    def _take_action(self, action):
        """根据action值控制电磁铁。"""
        if action == 18: # NO_OP
            # print("Action: NO_OP")
            return

        magnet_id = action % 9
        move = self.controller.ACTION_OUT if action >= 9 else self.controller.ACTION_IN

        # 只有在目标状态与当前状态不同时才执行动作
        if self.magnet_states[magnet_id] != move:
            self.controller._send_command(magnet_id, move)
            self.magnet_states[magnet_id] = move
            time.sleep(1) # 等待电磁铁动作完成

    def action_masks(self):
        """返回一个布尔掩码，指示哪些动作是有效的。"""
        mask = np.ones(19, dtype=bool)
        mask[18] = False  # NO_OP动作始终无效
        for i in range(9):
            # 如果磁铁i当前是IN状态(0)，则不能再执行IN动作
            if self.magnet_states[i] == self.controller.ACTION_IN:
                mask[i] = False
            # 如果磁铁i当前是OUT状态(1)，则不能再执行OUT动作
            else:
                mask[i + 9] = False
        return mask

    def _get_info(self):
        """返回附加信息，最重要的是提供合法的动作掩码。"""
        return {"action_mask": self.action_masks()}

    def reset(self, seed=None, options=None):
        """重置环境到初始状态。"""
        super().reset(seed=seed)
        
        # 重置所有电磁铁到'IN'状态
        for i in range(9):
            # if self.magnet_states[i] == self.controller.ACTION_OUT:
            self.controller.magnet_in(i)
            time.sleep(0.5)
        self.magnet_states.fill(0)

        self.current_step = 0
        
        observation = self._get_observation()
        info = self._get_info()
        
        return observation, info

    def close(self):
        """清理和关闭资源。"""
        print("正在关闭环境...")
        self.controller.disconnect()
        finalize_sensor()

if __name__ == '__main__':
    # --- 用于测试环境的示例代码 ---
    print("正在创建并测试DiffuserEnv...")
    env = DiffuserEnv(port='COM5')
    
    # 打印空间信息
    print("Action Space:", env.action_space)
    print("Observation Space:", env.observation_space)
    
    # 重置环境
    obs, info = env.reset()
    print("Initial Observation Shape:", obs.shape)
    print("Initial Action Mask:", info["action_mask"])
    
    # 执行一些随机的有效动作
    for i in range(5):
        print(f"\n--- Step {i+1} ---")
        # 从有效动作中随机选择一个
        valid_actions = np.where(env.action_masks())[0]
        action = np.random.choice(valid_actions)
        print(f"Taking action: {action}")
        
        obs, reward, terminated, truncated, info = env.step(action)
        
        print("Observation Shape:", obs.shape)
        print("Reward:", reward)
        print("Next Action Mask:", info["action_mask"])
        
        if terminated or truncated:
            print("Episode finished. Resetting...")
            obs, info = env.reset()

    # 关闭环境
    env.close()
    print("环境测试完成。")
