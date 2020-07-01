import numpy as np
import os
import gym
import gzip

from subprocess import Popen

URI = 'gs://atari-replay-datasets/dqn/{}/{}/replay_logs/'
BASE_DIR = os.path.join(os.environ['HOME'], '.d4rl', 'datasets')


def get_dir_path(env, index, epoch, base_dir=BASE_DIR):
    return os.path.join(base_dir, env, str(index), str(epoch))


def inspect_dir_path(env, index, epoch, base_dir=BASE_DIR):
    path = get_dir_path(env, index, epoch, base_dir)
    if not os.path.exists(path):
        return False
    for name in ['observation', 'action', 'reward', 'terminal']:
        if not os.path.exists(os.path.join(path, name + '.gz')):
            return False
    return True


def _download(name, env, index, epoch, dir_path):
    file_name = '$store$_{}_ckpt.{}.gz'.format(name, epoch)
    uri = URI.format(env, index) + file_name
    path = os.path.join(dir_path, '{}.gz'.format(name))
    p = Popen(['gsutil', '-m', 'cp', '-R', uri, path])
    p.wait()
    return path


def _load(name, dir_path):
    path = os.path.join(dir_path, name + '.gz')
    with gzip.open(path, 'rb') as f:
        print('loading {}...'.format(path))
        return np.load(f, allow_pickle=False)


def download_dataset(env, index, epoch, base_dir=BASE_DIR):
    dir_path = get_dir_path(env, index, epoch, base_dir)
    _download('observation', env, index, epoch, dir_path)
    _download('action', env, index, epoch, dir_path)
    _download('reward', env, index, epoch, dir_path)
    _download('terminal', env, index, epoch, dir_path)


class OfflineEnv(gym.Env):
    def __init__(self,
                 game=None,
                 index=None,
                 start_epoch=None,
                 last_epoch=None,
                 **kwargs):
        super(OfflineEnv, self).__init__(**kwargs)
        self.game = game
        self.index = index
        self.start_epoch = start_epoch
        self.last_epoch = last_epoch

    def get_dataset(self):
        observation_stack = []
        action_stack = []
        reward_stack = []
        terminal_stack = []
        for epoch in range(self.start_epoch, self.last_epoch + 1):
            path = get_dir_path(self.game, self.index, epoch)
            if not inspect_dir_path(self.game, self.index, epoch):
                os.makedirs(path, exist_ok=True)
                download_dataset(self.game, self.index, epoch)

            observations = _load('observation', path)
            actions = _load('action', path)
            rewards = _load('reward', path)
            terminals = _load('terminal', path)

            # sanity check
            assert observations.shape == (1000000, 84, 84)
            assert actions.shape == (1000000, )
            assert rewards.shape == (1000000, )
            assert terminals.shape == (1000000, )

            observation_stack.append(observations)
            action_stack.append(actions)
            reward_stack.append(rewards)
            terminal_stack.append(terminals)

        data_dict = {
            'observations': np.vstack(observation_stack),
            'actions': np.vstack(action_stack).reshape(-1),
            'rewards': np.vstack(reward_stack).reshape(-1),
            'terminals': np.vstack(terminal_stack).reshape(-1)
        }

        return data_dict
