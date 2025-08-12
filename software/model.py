import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque

class QNetwork(nn.Module):
    """一个简单的全连接神经网络，用于逼近Q函数"""
    def __init__(self, state_dim, action_dim):
        super(QNetwork, self).__init__()
        self.layer1 = nn.Linear(state_dim, 128)
        self.layer2 = nn.Linear(128, 128)
        self.layer3 = nn.Linear(128, action_dim)

    def forward(self, state):
        x = torch.relu(self.layer1(state))
        x = torch.relu(self.layer2(x))
        return self.layer3(x)

class ReplayBuffer:
    """经验回放缓冲区，用于存储和采样过去的经验"""
    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        # 将状态和下一个状态展平
        state = np.ravel(state)
        next_state = np.ravel(next_state)
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        states, actions, rewards, next_states, dones = zip(*random.sample(self.buffer, batch_size))
        return np.array(states), actions, rewards, np.array(next_states), dones

    def __len__(self):
        return len(self.buffer)

class DQNAgent:
    """DQN代理，负责决策和学习"""
    def __init__(self, state_dim, action_dim, replay_buffer_capacity=10000, batch_size=64, gamma=0.99, lr=1e-4, tau=0.005):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.batch_size = batch_size
        self.gamma = gamma
        self.tau = tau

        self.policy_net = QNetwork(state_dim, action_dim)
        self.target_net = QNetwork(state_dim, action_dim)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)
        self.replay_buffer = ReplayBuffer(replay_buffer_capacity)
        self.loss_fn = nn.MSELoss()

    def select_action(self, state, epsilon, action_mask):
        """使用epsilon-greedy策略选择一个动作，同时考虑动作掩码"""
        state = torch.FloatTensor(np.ravel(state)).unsqueeze(0)
        
        if random.random() > epsilon:
            with torch.no_grad():
                q_values = self.policy_net(state)
                # 将无效动作的Q值设置为负无穷大
                q_values[0, ~action_mask] = -float('inf')
                # 从有效动作中选择Q值最大的一个
                action = q_values.argmax().item()
        else:
            # 随机选择一个有效动作
            valid_actions = np.where(action_mask)[0]
            action = random.choice(valid_actions)
            
        return action

    def update_model(self):
        """从经验回放区采样并更新网络"""
        if len(self.replay_buffer) < self.batch_size:
            return None # 缓冲区中的样本不足

        states, actions, rewards, next_states, dones = self.replay_buffer.sample(self.batch_size)

        states = torch.FloatTensor(states)
        actions = torch.LongTensor(actions).unsqueeze(1)
        rewards = torch.FloatTensor(rewards).unsqueeze(1)
        next_states = torch.FloatTensor(next_states)
        dones = torch.FloatTensor(dones).unsqueeze(1)

        # 计算当前状态的Q值
        current_q_values = self.policy_net(states).gather(1, actions)

        # 计算下一个状态的最大Q值（使用目标网络）
        with torch.no_grad():
            next_q_values = self.target_net(next_states).max(1)[0].unsqueeze(1)
            
        # 计算期望的Q值
        expected_q_values = rewards + (1 - dones) * self.gamma * next_q_values

        # 计算损失
        loss = self.loss_fn(current_q_values, expected_q_values)

        # 优化模型
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # 软更新目标网络
        self._soft_update_target_net()
        
        return loss.item()

    def _soft_update_target_net(self):
        """软更新目标网络的权重"""
        for target_param, policy_param in zip(self.target_net.parameters(), self.policy_net.parameters()):
            target_param.data.copy_(self.tau * policy_param.data + (1.0 - self.tau) * target_param.data)

    def save(self, filepath):
        torch.save(self.policy_net.state_dict(), filepath)

    def load(self, filepath):
        self.policy_net.load_state_dict(torch.load(filepath))
        self.target_net.load_state_dict(torch.load(filepath))
