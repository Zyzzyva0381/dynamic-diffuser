import numpy as np
import time
from diffuser_env import DiffuserEnv

def set_and_evaluate(env, target_states):
    """
    Sets the magnets to a specific state, waits, gets an observation, and calculates the reward.

    Args:
        env (DiffuserEnv): The diffuser environment instance.
        target_states (np.array): A numpy array of 9 integers (0 for IN, 1 for OUT).

    Returns:
        float: The calculated reward for the given state.
    """
    print(f"Setting magnet states to: {target_states}...")
    
    # Set each magnet to the desired state
    for i in range(9):
        # Only send a command if the state needs to change
        if env.magnet_states[i] != target_states[i]:
            move = env.controller.ACTION_OUT if target_states[i] == 1 else env.controller.ACTION_IN
            env.controller._send_command(i, move)
            env.magnet_states[i] = target_states[i]
            time.sleep(1.0) # Wait for the magnet to move

    print("All magnets set. Acquiring data...")
    # Wait a moment for the sound field to stabilize before measuring
    time.sleep(2.0)

    # Get observation and calculate reward
    observation = env._get_observation()
    reward = env._calculate_reward(observation)
    
    return reward

def main():
    """
    Main function to compare rewards for two specific magnet configurations.
    """
    print("Initializing environment for reward comparison...")
    # Use the same port as in the environment's test script
    env = DiffuserEnv(port='COM5') 
    
    try:
        # --- State 1: All magnets extended (OUT) ---
        all_out_state = np.ones(9, dtype=int)
        reward_all_out = set_and_evaluate(env, all_out_state)
        print(f"\n--- Comparison Result ---")
        print(f"State 'All OUT' ({all_out_state}):")
        print(f"  - Diff: {reward_all_out:.4f}\n")

        # --- State 2: A single random static configuration ---
        # Reset magnets to a known state (all IN) before setting the random state
        print("Resetting magnets to 'All IN' before next test...")
        obs, info = env.reset() # reset returns obs and info
        
        random_state = np.random.randint(0, 2, size=9)
        reward_random = set_and_evaluate(env, random_state)
        print(f"State 'Random' ({random_state}):")
        print(f"  - Diff: {reward_random:.4f}\n")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Ensure the environment is closed properly
        env.close()
        print("Comparison finished and environment closed.")

if __name__ == '__main__':
    main()
