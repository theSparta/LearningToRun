import multiprocessing,time,random
from multiprocessing import Process, Pipe
from osim.env import RunEnv

# separate process that holds a separate RunEnv instance.
# This has to be done since RunEnv() in the same process result in interleaved running of simulations.
def standalone_headless_isolated(conn):
    from osim.env import RunEnv
    e = RunEnv(visualize=False)

    while True:
        msg = conn.recv()

        # messages should be tuples,
        # msg[0] should be string

        if msg[0] == 'reset':
            o = e.reset(difficulty=2, seed=msg[1])
            conn.send(o)
        elif msg[0] == 'step':
            ordi = e.step(msg[1])
            conn.send(ordi)
        elif msg[0] == 'sample':
            action = e.action_space.sample()
            conn.send(action)
        else:
            conn.close()
            del e
            return

# class that manages the interprocess communication and expose itself as a RunEnv.
class ei: # Environment Instance
    def __init__(self):
        self.pc, self.cc = Pipe()
        self.p = Process(
            target = standalone_headless_isolated,
            args=(self.cc,)
        )
        self.p.daemon = True
        self.p.start()

    def reset(self, seed):
        self.pc.send(('reset', seed,))
        return self.pc.recv()

    def step(self,actions):
        self.pc.send(('step',actions,))
        return self.pc.recv()

    def sample(self):
        self.pc.send(('sample',))
        return self.pc.recv()

    def __del__(self):
        self.pc.send(('exit',))
        print('(ei)waiting for join...')
        self.p.join()

counter = 0


def f((i,action)):
    observation, reward, done, info = env[i].step(action)
    return observation

if __name__ == '__main__':
    num = 1
    observation = [0]*num
    env = [0]*num
    actions = [None]*num

    for i in range(num):
        env[i] = ei()
        observation[i] = env[i].reset(i)

    actions = [env[i].sample() for i in range(num)]
    pool = multiprocessing.Pool(num)
    o = pool.map(f,  zip(range(num),actions))
    print(o)