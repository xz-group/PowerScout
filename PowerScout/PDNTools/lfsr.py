import numpy as np


class LinearFeedbackShiftRegister:
    PRBS_POLY_TABLE = {
        2: [2, 1],
        3: [3, 2],
        4: [4, 3],
        5: [5, 3],
        6: [6, 5],
        7: [7, 6],
        8: [8, 6, 5, 4],
        9: [9, 5],
        10: [10, 7],
        11: [11, 9],
        12: [12, 11, 8, 6],
        13: [13, 12, 11, 8],
        14: [14, 13, 12, 2],
        15: [15, 14],
        16: [16, 14, 13, 11],
        17: [17, 14],
        18: [18, 11],
        19: [19, 18, 17, 20],
        20: [20, 17],
        21: [21, 19],
        22: [22, 21],
        23: [23, 18],
        24: [24, 23, 21, 20],
        25: [25, 22],
        26: [26, 25, 24, 21, 20],
        27: [27, 26, 25, 22],
        28: [28, 25],
        29: [29, 27],
        30: [30, 29, 26, 24],
        31: [31, 28],
        32: [32, 30, 26, 25]
    }

    def __init__(self, fpoly=None, init_state='ones', m=None):
        if fpoly is None:
            fpoly = [5, 3]

        if m in self.PRBS_POLY_TABLE.keys():
            self.fb_poly = self.get_prbs_poly(m)
        else:
            self.fb_poly = fpoly

        if isinstance(init_state, str):
            if init_state == 'ones':
                init_state = np.ones(np.max(self.fb_poly))
            elif init_state == 'random':
                init_state = np.random.randint(0, 2, np.max(self.fb_poly))
            else:
                raise Exception('Unknown initial state')
        if isinstance(init_state, list):
            init_state = np.array(init_state)

        self.init_state = init_state
        self.state = init_state.astype(int)
        self.count = 0
        self.seq = np.array(-1)
        self.outbit = -1
        self.feedback_bit = -1
        self.M = self.init_state.shape[0]
        self.expectedPeriod = 2 ** self.M - 1
        self.fb_poly.sort(reverse=True)
        feed = ' '
        for i in range(len(self.fb_poly)):
            feed = feed + 'x^' + str(self.fb_poly[i]) + ' + '
        feed = feed + '1'
        self.feedpoly = feed
        self.check()

    def info(self):
        print('%d bit LFSR with feedback polynomial %s' % (self.M, self.feedpoly))
        print('Expected Period (if polynomial is primitive) = ', self.expectedPeriod)
        print('Current :')
        print(' State        : ', self.state)
        print(' Count        : ', self.count)
        print(' Output bit   : ', self.outbit)
        print(' feedback bit : ', self.feedback_bit)
        if self.count > 0 and self.count < 1000:
            print(' Output Sequence %s' % (''.join([str(int(x)) for x in self.seq])))

    def check(self):
        if np.max(self.fb_poly) > self.init_state.shape[0] or np.min(self.fb_poly) < 1 or len(self.fb_poly) < 2:
            raise ValueError('Wrong feedback polynomial')
        if len(self.init_state.shape) > 1 and (self.init_state.shape[0] != 1 or self.init_state.shape[1] != 1):
            raise ValueError('Size of intial state vector should be one diamensional')
        else:
            self.init_state = np.squeeze(self.init_state)

    def set(self, fpoly, state='ones'):
        self.__init__(fpoly=fpoly, init_state=state)

    def reset(self):
        self.__init__(init_state=self.init_state, fpoly=self.fb_poly)

    def changeFpoly(self, newfpoly, reset=False):
        newfpoly.sort(reverse=True)
        self.fb_poly = newfpoly
        feed = ' '
        for i in range(len(self.fb_poly)):
            feed = feed + 'x^' + str(self.fb_poly[i]) + ' + '
        feed = feed + '1'
        self.feedpoly = feed

        self.check()
        if reset:
            self.reset()

    def next(self):
        b = np.logical_xor(self.state[self.fb_poly[0] - 1], self.state[self.fb_poly[1] - 1])
        if len(self.fb_poly) > 2:
            for i in range(2, len(self.fb_poly)):
                b = np.logical_xor(self.state[self.fb_poly[i] - 1], b)

        self.state = np.roll(self.state, 1)
        self.state[0] = b * 1
        self.feedback_bit = b * 1
        if self.count == 0:
            self.seq = self.state[-1]
        else:
            self.seq = np.append(self.seq, self.state[-1])
        self.outbit = self.state[-1]
        self.count += 1
        return self.state[-1]

    def runFullCycle(self, k=1):
        for j in range(k):
            for i in range(self.expectedPeriod):
                self.next()
        return self.seq

    def runKCycle(self, k):
        tempseq = np.ones(k) * -1
        for i in range(k):
            tempseq[i] = self.next()

        return tempseq

    def get_prbs_poly(self, m):
        if m in self.PRBS_POLY_TABLE.keys():
            return self.PRBS_POLY_TABLE.get(m)
        else:
            raise ValueError

    def prbs_poly_table_check(self):
        for M in self.PRBS_POLY_TABLE.keys():
            self.set(self.get_prbs_poly(M))
            temp = list(self.runKCycle(self.expectedPeriod * 2))
            print(self.expectedPeriod)
            if temp[0:self.expectedPeriod] == \
                    temp[self.expectedPeriod:2 * self.expectedPeriod]:
                print("M=%d pass PRBS test." % M)
            else:
                raise ValueError("M=%d does not pass PRBS test." % M)
