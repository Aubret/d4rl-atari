
import gym
import d4rl_atari

from d4rl_atari.offline_env import _stack

def test_env():
    env = gym.make('space-invaders-expert-v0', stack=True)
    observation = env.reset()
    dataset = env.get_dataset()
    print(dataset["observations"].shape)
    print(dataset.keys)

if __name__ == '__main__':
    #mp.set_start_method('spawn', force=True)
    test_env()