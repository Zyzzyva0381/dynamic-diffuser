import numpy as np
import time
from diffuser_env import DiffuserEnv
from model import DQNAgent
from torch.utils.tensorboard import SummaryWriter

# --- 配置参数 ---
EPISODES = 500
MAX_STEPS_PER_EPISODE = 100
EPSILON_START = 1.0
EPSILON_END = 0.1
EPSILON_DECAY = 0.995
LEARNING_STARTS = 50 # 在开始学习前，先收集一些经验
MODEL_SAVE_PATH = "dqn_diffuser_model.pth"
LOG_DIR = "dqn_logs"

# --- 初始化 ---
env = DiffuserEnv(port='COM5')
# 将观测空间展平，所以状态维度是 10 * 3 = 30
state_dim = np.prod(env.observation_space.shape) 
action_dim = env.action_space.n
agent = DQNAgent(state_dim, action_dim)
writer = SummaryWriter(LOG_DIR)

epsilon = EPSILON_START
total_steps = 0

# --- 训练循环 ---
try:
    for episode in range(EPISODES):
        state, info = env.reset()
        episode_reward = 0
        
        for step in range(MAX_STEPS_PER_EPISODE):
            action_mask = info["action_mask"]
            
            # 在训练初期，随机探索
            if total_steps < LEARNING_STARTS:
                action = np.random.choice(np.where(action_mask)[0])
            else:
                action = agent.select_action(state, epsilon, action_mask)

            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated

            # 存储经验
            agent.replay_buffer.push(state, action, reward, next_state, done)

            # 如果收集到足够的经验，则更新模型
            if total_steps >= LEARNING_STARTS:
                loss = agent.update_model()
                if loss is not None:
                    writer.add_scalar('Loss', loss, total_steps)

            state = next_state
            episode_reward += reward
            total_steps += 1

            if done:
                break
        
        # 更新Epsilon
        epsilon = max(EPSILON_END, epsilon * EPSILON_DECAY)

        # 记录数据
        writer.add_scalar('Reward/Episode', episode_reward, episode)
        writer.add_scalar('Epsilon', epsilon, episode)
        print(f"Episode {episode}: Reward = {episode_reward:.2f}, Epsilon = {epsilon:.2f}, Steps = {step+1}")

        # 定期保存模型
        if episode % 50 == 0 and episode > 0:
            agent.save(f"dqn_model_episode_{episode}.pth")
            print(f"模型已保存: dqn_model_episode_{episode}.pth")

finally:
    # --- 清理 ---
    agent.save(MODEL_SAVE_PATH)
    print(f"训练结束，最终模型已保存至 {MODEL_SAVE_PATH}")
    env.close()
    writer.close()
