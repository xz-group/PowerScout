import re
from numpy import random
from PowerScout.PDNCircuit.Basic import *
from PowerScout.PDNTools.useful_tools import generate_waveform_from_amplitudes


class ChipSingleCore(SubCircuit, Block2Ports):
    DEFAULT_NAME = 'ChipSingleCore'

    __NODES = ()
    __Xstart = 1
    __Ystart = 1
    __Xstop = 3
    __Ystop = 3
    __C4numX = 1
    __C4numY = 1
    __C4shift = 0
    __Iload = [(2, 2)]
    __Iload_Flag = "Ideal_All"
    __PV_Group_Num = 1

    __Noise_Frequency = 1e6
    __Noise_Delay = 0
    __Noise_Group_Num = 1
    __Noise_Param1_List = 1
    __Noise_Param2_List = 0
    __Noise_Stop_Time = 0

    __Rdie = 50 @ u_mOhm
    __Ldie = 5.6e-6 @ u_nH
    __Cdie = 0.12 @ u_nF
    __Rbump = 1 @ u_Ohm
    __Lbump = 1 @ u_H
    __Rppkg = 0.5415 @ u_mOhm
    __Rspkg = 1 @ u_mOhm
    __Lppkg = 5.61 @ u_nH
    __Lspkg = 120 @ u_nH
    __Cppkg = 26 @ u_uF
    __Rro = 10 @ u_Ohm
    __waveform = []

    __nodes_power_grid = []
    __nodes_c4_vdd = []
    __nodes_c4_vss = []
    __nodes_load = []

    def __init__(self, pdn, name=None, waveform=None, **kwargs):
        if name is not None:
            self.sub_name = name
        else:
            self.sub_name = self.DEFAULT_NAME
        self.__waveform = waveform
        self.__nodes_power_grid = []
        self.__nodes_c4_vdd = []
        self.__nodes_c4_vss = []
        self.__nodes_load = []
        self.set_parameter(**kwargs)

        if re.match(r"^PV", self.__Iload_Flag, re.I):
            temp = []
            for i in range(self.__PV_Group_Num):
                temp.append('Ctrl_P' + str(i))
                temp.append('Ctrl_N' + str(i))
            Ctrl = tuple(temp)
            print(Ctrl)
            self.__NODES = self.NODES + Ctrl
        else:
            self.__NODES = self.NODES
        SubCircuit.__init__(self, self.sub_name, *self.__NODES)
        self._model()
        pdn.circuit.subcircuit(self)

    def set_parameter(self, **kwargs):
        self.__Xstop = kwargs.get('Xstop', self.__Xstop)
        self.__Ystop = kwargs.get('Ystop', self.__Ystop)
        self.__C4numX = kwargs.get('C4numX', self.__C4numX)
        self.__C4numY = kwargs.get('C4numY', self.__C4numY)
        self.__C4shift = kwargs.get('C4shift', self.__C4shift)
        self.__Iload_Flag = kwargs.get('IFlag', self.__Iload_Flag)
        self.__Iload = kwargs.get('Iload', self.__Iload)
        self.__PV_Group_Num = kwargs.get('PVgroupNum', self.__PV_Group_Num)
        self.__Rro = kwargs.get('Rro', self.__Rro)

        # For Noise Source
        self.__Noise_Frequency = kwargs.get('NoiseFreq', self.__Noise_Frequency)
        self.__Noise_Delay = kwargs.get('NoiseDelay', self.__Noise_Delay)
        self.__Noise_Stop_Time = kwargs.get('NoiseStopTime', self.__Noise_Stop_Time)
        self.__Noise_Param1_List = kwargs.get('NoiseUpperBoundList', self.__Noise_Param1_List)
        self.__Noise_Param2_List = kwargs.get('NoiseLowerBoundList', self.__Noise_Param2_List)
        if re.match(r"^Noise", self.__Iload_Flag, re.I):
            len_ = len(self.__Iload)
            if len_ != len(self.__Noise_Param1_List) or len_ != len(self.__Noise_Param2_List):
                raise Warning("Un-matched lengths for Noise source.")

        self.__Rbump = kwargs.get('Rbump', self.__Rbump)
        self.__Lbump = kwargs.get('Lbump', self.__Lbump)
        self.__Rppkg = kwargs.get('Rppkg', self.__Rppkg)
        self.__Rspkg = kwargs.get('Rspkg', self.__Rspkg)
        self.__Lspkg = kwargs.get('Lspkg', self.__Lspkg)
        self.__Lppkg = kwargs.get('Lppkg', self.__Lppkg)
        self.__Cppkg = kwargs.get('Cppkg', self.__Cppkg)
        self.__Rdie = kwargs.get('Rdie', self.__Rdie)
        self.__Ldie = kwargs.get('Ldie', self.__Ldie)
        self.__Cdie = kwargs.get('Cdie', self.__Cdie)

    def _model(self):
        # generate nodes
        x = np.arange(self.__Xstart, self.__Xstop + 1) * 10
        y = np.arange(self.__Ystart, self.__Ystop + 1) * 10
        if self.__C4numX < self.__Xstop:
            x_c4 = np.rint(np.linspace(self.__Xstart, self.__Xstop, self.__C4numX + 2)) * 10
            x_c4 = x_c4[1:-1]
        else:
            x_c4 = x

        if self.__C4numY < self.__Ystop:
            y_c4 = np.rint(np.linspace(self.__Ystart, self.__Ystop, self.__C4numY + 2)) * 10
            y_c4 = y_c4[1:-1]
        else:
            y_c4 = y

        if x_c4[-1] + self.__C4shift > x[-1] or y_c4[-1] + self.__C4shift > y[-1]:
            print('C4shift value exceeds. Set C4shift to 0.')
            self.__C4shift = 0

        self.__nodes_power_grid = [x, y]
        self.__nodes_c4_vdd = [x_c4, y_c4]
        self.__nodes_c4_vss = [x_c4 + self.__C4shift * 10, y_c4 + self.__C4shift * 10]

        for node in self.__Iload:
            if self.__Xstart <= node[0] <= self.__Xstop and self.__Ystart <= node[1] <= self.__Ystop:
                self.__nodes_load.append(node)
            else:
                print("Wrong Iload position of (%d,%d)! Position should be between %d and %d for X, %d and %d for Y",
                      node[0], node[1], self.__Xstart, self.__Xstop, self.__Ystart, self.__Ystop)
                exit("Error")

        # generate power grid - horizontal line
        for j in range(len(self.__nodes_power_grid[1])):  # Y
            for i in range(len(self.__nodes_power_grid[0]) - 1):  # X
                self._implement_die_grid(i, j, flag="horizontal")

        # generate power grid - vertical line
        for i in range(len(self.__nodes_power_grid[0])):  # X
            for j in range(len(self.__nodes_power_grid[1]) - 1):  # Y
                self._implement_die_grid(i, j, flag="vertical")

        # generate power grid - node capacitor
        for i in range(len(self.__nodes_power_grid[0])):  # X
            for j in range(len(self.__nodes_power_grid[1])):  # Y
                self._implement_die_cap(i, j)

        # implement load source
        if re.match("Ideal", self.__Iload_Flag, re.I):  # from "Yes"
            for node in self.__nodes_load:
                self._implement_die_load(node[0], node[1])
        elif re.match("None", self.__Iload_Flag, re.I):  # from "No"
            self.__nodes_load = []
        elif re.match("Ideal_All", self.__Iload_Flag, re.I):  # from "ALL"
            for i in range(len(self.__nodes_power_grid[0])):  # X
                for j in range(len(self.__nodes_power_grid[1])):  # Y
                    self._implement_die_load(i, j)
                    self.__nodes_load.append((i, j))
        elif re.match("PV_ALL", self.__Iload_Flag, re.I):  # from "PV"
            self.model('Switch', 'SW', ron=self.__Rro, roff=1e12, vt=0.5)
            num_temp = self.__PV_Group_Num - 1
            for i in range(len(self.__nodes_power_grid[0])):  # X
                for j in range(len(self.__nodes_power_grid[1])):  # Y
                    num_temp += 1
                    self._implement_power_virus(i, j, num_temp % self.__PV_Group_Num)
                    self.__nodes_load.append((i, j))
        # todo: add PV to separately set the PV
        elif re.match("AES_ALL", self.__Iload_Flag, re.I):
            for i in range(len(self.__nodes_power_grid[0])):  # X
                for j in range(len(self.__nodes_power_grid[1])):  # Y
                    self._implement_aes(i, j, self.__waveform)
                    self.__nodes_load.append((i, j))
        elif re.match("AES", self.__Iload_Flag, re.I):
            for node in self.__nodes_load:
                self._implement_aes(node[0], node[1], self.__waveform)
        elif re.match("NOISE", self.__Iload_Flag, re.I):
            for index, node in enumerate(self.__nodes_load):
                self._implement_noise_current_source(node[0], node[1],
                                                     frequency=self.__Noise_Frequency,
                                                     delay=self.__Noise_Delay,
                                                     upper_bound=self.__Noise_Param1_List[index],
                                                     lower_bound=self.__Noise_Param2_List[index],
                                                     stop_time=self.__Noise_Stop_Time)
        else:
            exit("Wrong Iload Flag!")

        # implement C4 bumps
        self._implement_c4()

        # implement package
        self._implement_pkg_series(flag="VDD")
        self._implement_pkg_series(flag="VSS")
        self._implement_pkg_parallel(2)

    def _implement_die_grid(self, i, j, flag='None'):
        if re.match("Vertical", flag, re.I):
            a = i
            b = j + 1
        elif re.match("Horizontal", flag, re.I):
            a = i + 1
            b = j
        else:
            a = 0
            b = 0
            exit("Wrong flag! Choose from Vertical or Horizontal")

        # VDD
        node_temp_10 = self._pos2nodes(self.__nodes_power_grid[0][i], self.__nodes_power_grid[1][j], flag='VDD')
        node_temp_15 = self._pos2nodes((self.__nodes_power_grid[0][i] + self.__nodes_power_grid[0][a]) / 2,
                                       (self.__nodes_power_grid[1][j] + self.__nodes_power_grid[1][b]) / 2, flag='VDD')
        node_temp_20 = self._pos2nodes(self.__nodes_power_grid[0][a], self.__nodes_power_grid[1][b], flag='VDD')
        name_temp = '_' + node_temp_10 + '_' + node_temp_20
        self.R(name_temp, node_temp_10, node_temp_15, self.__Rdie)
        self.L(name_temp, node_temp_15, node_temp_20, self.__Ldie)

        # VSS
        node_temp_10 = self._pos2nodes(self.__nodes_power_grid[0][i], self.__nodes_power_grid[1][j], flag='VSS')
        node_temp_15 = self._pos2nodes((self.__nodes_power_grid[0][i] + self.__nodes_power_grid[0][a]) / 2,
                                       (self.__nodes_power_grid[1][j] + self.__nodes_power_grid[1][b]) / 2, flag='VSS')
        node_temp_20 = self._pos2nodes(self.__nodes_power_grid[0][a], self.__nodes_power_grid[1][b], flag='VSS')
        name_temp = '_' + node_temp_10 + '_' + node_temp_20
        self.R(name_temp, node_temp_10, node_temp_15, self.__Rdie)
        self.L(name_temp, node_temp_15, node_temp_20, self.__Ldie)

    def _implement_die_cap(self, i, j):
        node_temp_10 = self._pos2nodes(self.__nodes_power_grid[0][i], self.__nodes_power_grid[1][j], flag='VDD')
        node_temp_20 = self._pos2nodes(self.__nodes_power_grid[0][i], self.__nodes_power_grid[1][j], flag='VSS')
        name_temp = '_' + node_temp_10 + '_' + node_temp_20
        self.C(name_temp, node_temp_10, node_temp_20, self.__Cdie)

    def _implement_die_load(self, i, j):
        node_temp_10 = self._pos2nodes(self.__nodes_power_grid[0][i - 1], self.__nodes_power_grid[1][j - 1], flag='VDD')
        node_temp_20 = self._pos2nodes(self.__nodes_power_grid[0][i - 1], self.__nodes_power_grid[1][j - 1], flag='VSS')
        name_temp = '_' + node_temp_10 + '_' + node_temp_20
        # Ngspice Manual A current source of positive value forces current to flow out of the n+ node,
        # through the source, and into the n- node.
        amp = 1 / len(self.__nodes_power_grid[0]) / len(self.__nodes_power_grid[1])
        self.I(name_temp, node_temp_10, node_temp_10 + 'DM', 1, AC=amp)
        # it is used to sense the current so that support CCCS.
        self.V(name_temp, node_temp_10 + 'DM', node_temp_20, 0)
        # self.I(name_temp, node_temp_10, node_temp_20, 1, AC=1)

    def _implement_power_virus(self, i, j, group_num):
        node_temp_10 = self._pos2nodes(self.__nodes_power_grid[0][i - 1], self.__nodes_power_grid[1][j - 1], flag='VDD')
        node_temp_20 = self._pos2nodes(self.__nodes_power_grid[0][i - 1], self.__nodes_power_grid[1][j - 1], flag='VSS')
        name_temp = '_' + node_temp_10 + '_' + node_temp_20
        self.VCS(name_temp, node_temp_10, node_temp_20, 'Ctrl_P' + str(group_num), 'Ctrl_N' + str(group_num),
                 model='Switch', initial_state='off')

    def _implement_noise_current_source(self, i, j, frequency, upper_bound, lower_bound, stop_time, delay=0):
        node_temp_10 = self._pos2nodes(self.__nodes_power_grid[0][i - 1], self.__nodes_power_grid[1][j - 1], flag='VDD')
        node_temp_20 = self._pos2nodes(self.__nodes_power_grid[0][i - 1], self.__nodes_power_grid[1][j - 1], flag='VSS')
        name_temp = '_' + node_temp_10 + '_' + node_temp_20
        self.PieceWiseLinearVoltageSource(name_temp + '_CTRL', node_temp_10 + '_CTRL', node_temp_20 + '_CTRL',
                                          self._generate_random_waveform(
                                              random_type='uniform',
                                              frequency=frequency,
                                              time_delay=delay,
                                              param1=upper_bound,
                                              param2=lower_bound,
                                              stop_time=stop_time))
        self.VoltageControlledCurrentSource(name_temp, node_temp_10, node_temp_20,
                                            node_temp_10 + '_CTRL', node_temp_20 + '_CTRL',
                                            1)

    @staticmethod
    def _generate_random_waveform(frequency, time_delay, param1, param2, stop_time, random_type='uniform', seed=None):
        total_num_states = int(frequency * stop_time)
        random_states = []
        # get the seed
        if seed is None:
            random.default_rng(int(time.time()))
        else:
            random.default_rng(seed)

        if re.match('uniform', random_type, re.I):
            random_states = random.uniform(param1, param2, int(total_num_states * 1.1)).tolist()

        waveform = generate_waveform_from_amplitudes(random_states, frequency, time_delay, stop_time,
                                                     dt=0.01 / frequency)
        return waveform

    def _implement_aes(self, i, j, waveform):
        node_temp_10 = self._pos2nodes(self.__nodes_power_grid[0][i - 1], self.__nodes_power_grid[1][j - 1], flag='VDD')
        node_temp_20 = self._pos2nodes(self.__nodes_power_grid[0][i - 1], self.__nodes_power_grid[1][j - 1], flag='VSS')
        name_temp = '_' + node_temp_10 + '_' + node_temp_20
        self.PieceWiseLinearCurrentSource(name_temp, node_temp_10, node_temp_20, waveform, dc=0)

    def _implement_c4(self):
        # implement C4 bumps
        nodes_c4_str = []
        for i in range(len(self.__nodes_c4_vdd[0])):
            for j in range(len(self.__nodes_c4_vdd[1])):
                nodes_c4_str.append(self._pos2nodes(self.__nodes_c4_vdd[0][i], self.__nodes_c4_vdd[1][j], flag='VDD'))
                nodes_c4_str.append(self._pos2nodes(self.__nodes_c4_vss[0][i], self.__nodes_c4_vss[1][j], flag='VSS'))

        for node in nodes_c4_str:
            temp = ""
            if "VDD" in node:
                temp = "VDD"
            elif "VSS" in node:
                temp = "VSS"

            self.R('bump_' + node, node, node + 'M', self.__Rbump)
            self.L('bump_' + node, node + 'M', temp + "2", self.__Lbump)

    @property
    def nodes_pool_grid(self):
        temp = []
        for j in range(len(self.__nodes_power_grid[1])):  # Y
            for i in range(len(self.__nodes_power_grid[0])):  # X
                temp1 = self._name + '.' + self._pos2nodes(self.__nodes_power_grid[0][i], self.__nodes_power_grid[1][j],
                                                           'None')
                temp2 = self._name + '.' + self._pos2nodes(self.__nodes_power_grid[0][i], self.__nodes_power_grid[1][j],
                                                           'VDD')
                temp3 = self._name + '.' + self._pos2nodes(self.__nodes_power_grid[0][i], self.__nodes_power_grid[1][j],
                                                           'VSS')
                temp.append([temp1, temp2, temp3])
        return temp

    @property
    def nodes_pool_c4(self):
        temp = []
        for j in range(len(self.__nodes_c4_vdd[1])):  # Y
            for i in range(len(self.__nodes_c4_vdd[0])):  # X
                temp1 = self._name + '.' + 'bump' + '.' + self._pos2nodes(self.__nodes_c4_vdd[0][i],
                                                                          self.__nodes_c4_vdd[1][j],
                                                                          'None') + self._pos2nodes(
                    self.__nodes_c4_vss[0][i],
                    self.__nodes_c4_vss[1][j], 'None')
                temp2 = self._name + '.' + self._pos2nodes(self.__nodes_c4_vdd[0][i], self.__nodes_c4_vdd[1][j], 'VDD')
                temp3 = self._name + '.' + self._pos2nodes(self.__nodes_c4_vss[0][i], self.__nodes_c4_vss[1][j], 'VSS')
                temp.append([temp1, temp2, temp3])
        return temp

    @property
    def nodes_pool_load(self):
        temp = []
        if self.__nodes_load:
            for node in self.__nodes_load:
                temp1 = self._name + '.' + 'load' + '.' + self._pos2nodes(self.__nodes_power_grid[0][node[0] - 1],
                                                                          self.__nodes_power_grid[1][node[1] - 1],
                                                                          'None')
                temp2 = self._pos2nodes(self.__nodes_power_grid[0][node[0] - 1],
                                        self.__nodes_power_grid[1][node[1] - 1], flag='VDD')
                temp3 = self._pos2nodes(self.__nodes_power_grid[0][node[0] - 1],
                                        self.__nodes_power_grid[1][node[1] - 1], flag='VSS')
                temp.append([temp1, temp2, temp3])
        return temp

    def _implement_pkg_series(self, flag="None"):
        if re.match("VDD", flag, re.I):
            temp = 'VDD'
        elif re.match("VSS", flag, re.I):
            temp = 'VSS'
        else:
            temp = 'None'
            exit("Wrong flag! Choose from VDD or VSS.")

        self.R("s" + temp, temp, temp + "MS", self.__Rspkg)
        self.L("s" + temp, temp + "MS", temp + "2", self.__Lspkg)

    def _implement_pkg_parallel(self, node_num):
        temp_00 = "VDD" + str(node_num)
        temp_01 = temp_00 + "M"
        temp_10 = "VSS" + str(node_num)
        temp_11 = temp_10 + "M"
        self.R("p", temp_00, temp_01, self.__Rppkg)
        self.L("p", temp_10, temp_11, self.__Lppkg)
        self.C("p", temp_01, temp_11, self.__Cppkg)

    @staticmethod
    def update_nodes_pool(pdn, nodes):
        pdn.nodes_pool.extend(nodes)

    @staticmethod
    def _pos2nodes(x, y, flag='None'):
        if re.match("VDD", flag, re.I):
            return 'X' + str(int(x)) + 'Y' + str(int(y)) + 'VDD'
        elif re.match("VSS", flag, re.I):
            return 'X' + str(int(x)) + 'Y' + str(int(y)) + 'VSS'
        elif re.match("None", flag, re.I):
            return 'X' + str(int(x)) + 'Y' + str(int(y))
        else:
            print("Wrong flag! Choose from VDD or VSS.")

    def implement(self, pdn, *args, br_flag="", chip_id=""):
        NODES = list(self.__NODES)
        for i in range(2):  # just for VDD and VSS
            NODES[i] = NODES[i] + str(pdn.nodes_count) + br_flag
        pdn.circuit.X(self.sub_name + str(chip_id) + br_flag, self.sub_name, *tuple(NODES))
        self._append_nodes_pair(pdn, br_flag)


class ChipLumped(SubCircuit, Block2Ports):
    DEFAULT_NAME = 'ChipLumped'

    __Iload_Flag = "All"
    __Rdie = 50 @ u_mOhm
    __Cdie = 0.12 @ u_nF
    __Rbump = 1 @ u_Ohm
    __Lbump = 1 @ u_H
    __Rppkg = 0.5415 @ u_mOhm
    __Rspkg = 1 @ u_mOhm
    __Lppkg = 5.61 @ u_nH
    __Lspkg = 120 @ u_nH
    __Cppkg = 26 @ u_uF

    __nodes_power_grid = []
    __nodes_c4_vdd = []
    __nodes_c4_vss = []
    __nodes_load = []

    def __init__(self, pdn, name=None, **kwargs):
        if name is not None:
            self.sub_name = name
        else:
            self.sub_name = self.DEFAULT_NAME
        self.set_parameter(**kwargs)
        self.__NODES = self.NODES
        SubCircuit.__init__(self, self.sub_name, *self.__NODES)
        self._model()
        pdn.circuit.subcircuit(self)

    def set_parameter(self, **kwargs):
        self.__Iload_Flag = kwargs.get('IFlag', self.__Iload_Flag)
        self.__Rbump = kwargs.get('Rbump', self.__Rbump)
        self.__Lbump = kwargs.get('Lbump', self.__Lbump)
        self.__Rppkg = kwargs.get('Rppkg', self.__Rppkg)
        self.__Rspkg = kwargs.get('Rspkg', self.__Rspkg)
        self.__Lspkg = kwargs.get('Lspkg', self.__Lspkg)
        self.__Lppkg = kwargs.get('Lppkg', self.__Lppkg)
        self.__Cppkg = kwargs.get('Cppkg', self.__Cppkg)
        self.__Rdie = kwargs.get('Rdie', self.__Rdie)
        self.__Cdie = kwargs.get('Cdie', self.__Cdie)

    def _model(self):
        # implement die
        die_name = self._implement_die()

        # implement load
        if re.match("Yes", self.__Iload_Flag, re.I):
            self._implement_load(name_pre=die_name)

        # implement C4 bumps
        self._implement_c4(flag="VDD", name_pre=die_name)
        self._implement_c4(flag="VSS", name_pre=die_name, zero_path=False)

        # implement package
        self._implement_pkg_series(flag="VDD")
        self._implement_pkg_series(flag="VSS")
        self._implement_pkg_parallel(2)

    def _implement_die(self):
        # implement dumped die
        name = 'die'
        self.R(name + 'VDD', name + 'VDD', name + 'capVDD', self.__Rdie)
        self.C(name, name + 'capVDD', name + "capVSS", self.__Cdie)
        self.R(name + 'VSS', name + 'capVSS', name + 'VSS', self.__Rdie)
        # self.R(name + 'VSS', name + 'capVSS', name + 'VSS', 0)
        return name

    def _implement_c4(self, flag="None", name_pre='None', zero_path=False):
        # implement lumped C4 bumps
        if re.match("VDD", flag, re.I):
            temp = 'VDD'
        elif re.match("VSS", flag, re.I):
            temp = 'VSS'
        else:
            temp = 'None'
            exit("Wrong flag! Choose from VDD or VSS.")

        if zero_path is False:
            self.R('bump_' + temp, name_pre + temp, temp + 'M', self.__Rbump)
            self.L('bump_' + temp, temp + 'M', temp + "2", self.__Lbump)
        else:
            self.R('bump_' + temp, name_pre + temp, temp + 'M', 0)
            self.L('bump_' + temp, temp + 'M', temp + "2", 0)

    def _implement_pkg_series(self, flag="None"):
        if re.match("VDD", flag, re.I):
            temp = 'VDD'
        elif re.match("VSS", flag, re.I):
            temp = 'VSS'
        else:
            temp = 'None'
            exit("Wrong flag! Choose from VDD or VSS.")

        self.R("pkgs_" + temp, temp, temp + "MS", self.__Rspkg)
        self.L("pkgs_" + temp, temp + "MS", temp + "2", self.__Lspkg)

    def _implement_pkg_parallel(self, node_num):
        temp_00 = "VDD" + str(node_num)
        temp_01 = temp_00 + "M"
        temp_10 = "VSS" + str(node_num)
        temp_11 = temp_10 + "M"
        self.R("pkgp", temp_00, temp_01, self.__Rppkg)
        self.L("pkgp", temp_10, temp_11, self.__Lppkg)
        self.C("pkgp", temp_01, temp_11, self.__Cppkg)

    def _implement_load(self, name_pre='None'):
        name = name_pre + 'load'
        node_temp_10 = name_pre + 'cap' + 'VDD'
        node_temp_20 = name_pre + 'cap' + 'VSS'
        # node_temp_10 = name_pre + 'VDD'
        # node_temp_20 = name_pre + 'VSS'
        # Ngspice Manual A current source of positive value forces current to flow out of the n+ node,
        # through the source, and into the n- node.
        self.I(name, node_temp_10, node_temp_10 + 'DM', 1, AC=1)
        # it is used to sense the current so that support CCCS.
        self.V(name, node_temp_10 + 'DM', node_temp_20, 0)
        # self.I(name_temp, node_temp_10, node_temp_20, 1, AC=1)

    def implement(self, pdn, *args, br_flag="", chip_id=""):
        NODES = list(self.__NODES)
        for i in range(2):  # just for VDD and VSS
            NODES[i] = NODES[i] + str(pdn.nodes_count) + br_flag
        pdn.circuit.X(self.sub_name + str(chip_id) + br_flag, self.sub_name, *tuple(NODES))
        self._append_nodes_pair(pdn, br_flag)


class ChipMultipleCore(SubCircuit, Block2Ports):
    DEFAULT_NAME = 'Core'

    __NODES = ()
    __Xstart = 1
    __Ystart = 1
    __Xstop = 3
    __Ystop = 3
    __C4numX = 1
    __C4numY = 1
    __C4shift = 0
    __Iload = [(2, 2)]
    __Iload_Flag = "All"
    __Rdie = 50 @ u_mOhm
    __Ldie = 5.6e-6 @ u_nH
    __Cdie = 0.12 @ u_nF
    __Load_type = 'Current'
    # parameters for IVR
    __Ivr_flag = 'No'
    __Ivr_feedback_flag = 'No'
    __Ivr_type = 'SC'
    __Req1 = 0.018 @ u_Ohm
    __Req2 = 0.018 @ u_Ohm
    __alpha = 1 / 3
    __Ceq = 394 @ u_nF
    __Cout = 320 @ u_nF
    __Leq = 6.25e-11
    __Rg = 0.025 @ u_Ohm
    __Vref_flag = 'Internal'
    __Vref = 1.1 @ u_V
    __k = 1

    __nodes_power_grid = []
    __nodes_c4_vdd = []
    __nodes_c4_vss = []
    __nodes_load = []

    def __init__(self, pdn, name=None, **kwargs):
        if name is not None:
            self.sub_name = name
        else:
            self.sub_name = self.DEFAULT_NAME
        self.set_parameter(**kwargs)
        self.set_parameter_ivr(**kwargs)
        self._generate_nodes()
        if re.match('Yes', self.__Ivr_flag, re.I):
            if re.match('External', self.__Vref_flag, re.I):
                nodes_ref = []
                for i in range(len(self._nodes_pool_c4_inout(mode=1))):
                    temp = '_' + str(i + 1)
                    nodes_ref.append("Vref" + temp)
                self.__NODES = self.NODES + tuple(nodes_ref)

            elif re.match('Internal', self.__Vref_flag, re.I):
                self.__NODES = self.NODES

            SubCircuit.__init__(self, self.sub_name, *self.__NODES)
            self._model()
            self._model_ivr_multiple()
        else:
            SubCircuit.__init__(self, self.sub_name, *tuple(self._nodes_pool_c4_inout()))
            self._model()
        pdn.circuit.subcircuit(self)

    def set_parameter(self, **kwargs):
        self.__Xstop = kwargs.get('Xstop', self.__Xstop)
        self.__Ystop = kwargs.get('Ystop', self.__Ystop)
        self.__C4numX = kwargs.get('C4numX', self.__C4numX)
        self.__C4numY = kwargs.get('C4numY', self.__C4numY)
        self.__C4shift = kwargs.get('C4shift', self.__C4shift)
        self.__Iload_Flag = kwargs.get('IFlag', self.__Iload_Flag)
        self.__Iload = kwargs.get('Iload', self.__Iload)
        self.__Rdie = kwargs.get('Rdie', self.__Rdie)
        self.__Ldie = kwargs.get('Ldie', self.__Ldie)
        self.__Cdie = kwargs.get('Cdie', self.__Cdie)
        self.__Ivr_flag = kwargs.get('IVRFlag', self.__Ivr_flag)
        self.__Vref_flag = kwargs.get('IVRRef', self.__Vref_flag)
        self.__Load_type = kwargs.get('LoadType', self.__Load_type)

    def set_parameter_ivr(self, **kwargs):
        self.__Req1 = kwargs.get('Req1', self.__Req1)
        self.__Req2 = kwargs.get('Req2', self.__Req2)
        self.__alpha = kwargs.get('alpha', self.__alpha)
        self.__Ceq = kwargs.get('Ceq', self.__Ceq)
        self.__Leq = kwargs.get('Leq', self.__Leq)
        self.__Cout = kwargs.get('Cout', self.__Cout)
        self.__Rg = kwargs.get('Rg', self.__Rg)
        self.__Vref = kwargs.get('Vref', self.__Vref)
        self.__k = kwargs.get('k', self.__k)
        self.__Ivr_feedback_flag = kwargs.get('IVRFb', self.__Ivr_feedback_flag)
        self.__Ivr_type = kwargs.get('IVRtype', self.__Ivr_type)

    def _generate_nodes(self):
        # generate nodes
        x = np.arange(self.__Xstart, self.__Xstop + 1) * 10
        y = np.arange(self.__Ystart, self.__Ystop + 1) * 10
        if self.__C4numX < self.__Xstop:
            x_c4 = np.rint(np.linspace(self.__Xstart, self.__Xstop, self.__C4numX + 2)) * 10
            x_c4 = x_c4[1:-1]
        else:
            x_c4 = x

        if self.__C4numY < self.__Ystop:
            y_c4 = np.rint(np.linspace(self.__Ystart, self.__Ystop, self.__C4numY + 2)) * 10
            y_c4 = y_c4[1:-1]
        else:
            y_c4 = y

        if x_c4[-1] + self.__C4shift > x[-1] or y_c4[-1] + self.__C4shift > y[-1]:
            print('C4shift value exceeds. Set C4shift to 0.')
            self.__C4shift = 0

        self.__nodes_power_grid = [x, y]
        self.__nodes_c4_vdd = [x_c4, y_c4]
        self.__nodes_c4_vss = [x_c4 + self.__C4shift * 10, y_c4 + self.__C4shift * 10]

        for node in self.__Iload:
            if self.__Xstart <= node[0] <= self.__Xstop and self.__Ystart <= node[1] <= self.__Ystop:
                self.__nodes_load.append(node)
            else:
                print("Wrong Iload position of (%d,%d)! Position should be between %d and %d for X, %d and %d for Y",
                      node[0], node[1], self.__Xstart, self.__Xstop, self.__Ystart, self.__Ystop)
                exit("Error")

    def _model(self):
        # generate power grid - horizontal line
        for j in range(len(self.__nodes_power_grid[1])):  # Y
            for i in range(len(self.__nodes_power_grid[0]) - 1):  # X
                self._implement_die_grid(i, j, flag="horizontal")

        # generate power grid - vertical line
        for i in range(len(self.__nodes_power_grid[0])):  # X
            for j in range(len(self.__nodes_power_grid[1]) - 1):  # Y
                self._implement_die_grid(i, j, flag="vertical")

        # generate power grid - node capacitor
        for i in range(len(self.__nodes_power_grid[0])):  # X
            for j in range(len(self.__nodes_power_grid[1])):  # Y
                self._implement_die_cap(i, j)

        # implement load source
        if re.match("Current", self.__Load_type, re.I):
            if re.match("Yes", self.__Iload_Flag, re.I):
                for node in self.__nodes_load:
                    self._implement_die_load(node[0], node[1])
            elif re.match("No", self.__Iload_Flag, re.I):
                for i in range(len(self.__nodes_power_grid[0])):  # X
                    for j in range(len(self.__nodes_power_grid[1])):  # Y
                        self._implement_die_load(i, j, load_flag=0)
                self.__nodes_load = []
            elif re.match("All", self.__Iload_Flag, re.I):
                for i in range(len(self.__nodes_power_grid[0])):  # X
                    for j in range(len(self.__nodes_power_grid[1])):  # Y
                        self._implement_die_load(i, j)
                        self.__nodes_load.append((i, j))
            else:
                exit("Wrong Iload Flag! Choose from Yes or No")

        elif re.match("Resistor", self.__Load_type, re.I):
            if re.match("Yes", self.__Iload_Flag, re.I):
                for node in self.__nodes_load:
                    self._implement_die_load_res(node[0], node[1])
            elif re.match("No", self.__Iload_Flag, re.I):
                self.__nodes_load = []
            elif re.match("All", self.__Iload_Flag, re.I):
                for i in range(len(self.__nodes_power_grid[0])):  # X
                    for j in range(len(self.__nodes_power_grid[1])):  # Y
                        self._implement_die_load_res(i, j)
                        self.__nodes_load.append((i, j))
            else:
                exit("Wrong Iload Flag! Choose from Yes or No")

    def _model_ivr_sc_single(self, count, output_pos, output_neg):
        temp = '_' + str(count)
        self.R('s1' + temp, 'VDD', '11' + temp, self.__Req1 / self.__alpha)
        self.C('p1' + temp, '11' + temp, 'VSS', self.__Ceq * self.__alpha)
        self.R('s2' + temp, '11' + temp, '12' + temp, self.__Req2 / self.__alpha)
        self.C('p2' + temp, '12' + temp, 'VSS', self.__Cout * self.__alpha)
        # self.R('p1', '12', 'VSS1', 1 / self.__alpha)
        self.CurrentControlledCurrentSource('s' + temp, '12' + temp, 'VSS', 'V_' + output_pos + '_' + output_neg,
                                            1 / self.__alpha)
        # self.CurrentControlledCurrentSource('s', '12', 'VSS', self.__Vnam, 1 / self.__alpha*12*12)
        self.R('g' + temp, 'VSS', output_neg, self.__Rg)
        self.VoltageControlledVoltageSource('s' + temp, '13' + temp, output_neg, 'VDD', 'VSS', self.__alpha)
        self.R('s3' + temp, '13' + temp, '14' + temp, self.__Req1)
        self.C('p3' + temp, '14' + temp, output_neg, self.__Ceq)
        self.R('s4' + temp, '14' + temp, output_pos, self.__Req2)
        self.C('p4' + temp, output_pos, output_neg, self.__Cout)

    def _model_ivr_single_buck_feedback(self, count, output_pos, output_neg):
        temp = '_' + str(count)
        self.R('s1' + temp, 'VDD', '11' + temp, self.__Req1 / self.__alpha)
        self.C('p1' + temp, '11' + temp, 'VSS', self.__Ceq * self.__alpha)
        self.R('s2' + temp, '11' + temp, '12' + temp, self.__Req2 / self.__alpha)
        self.C('p2' + temp, '12' + temp, 'VSS', self.__Cout * self.__alpha)
        # self.R('p1', '12', 'VSS1', 1 / self.__alpha)
        self.CurrentControlledCurrentSource('s' + temp, '12' + temp, 'VSS', 'V_' + output_pos + '_' + output_neg,
                                            1 / self.__alpha)
        # self.CurrentControlledCurrentSource('s', '12', 'VSS', self.__Vnam, 1 / self.__alpha*12*12)
        self.R('g' + temp, 'VSS', output_neg, self.__Rg)
        # self.VoltageControlledVoltageSource('s', '13', 'VSS2', 'VDD1', 'VSS1', self.__alpha)
        self.B('s' + temp, '13' + temp, output_neg, v=self._alpha_expression(output_pos, output_neg, "Vref" + temp))
        self.I('ac' + temp, '13' + temp, output_neg, 0, AC=1)
        self.R('s3' + temp, '13' + temp, '14' + temp, self.__Req1)
        # self.C('p3' + temp, '14' + temp, output_neg, self.__Ceq)
        self.L('s4' + temp, '14' + temp, output_pos, self.__Leq)
        self.C('p4' + temp, output_pos, output_neg, self.__Cout)
        if re.match('Internal', self.__Vref_flag, re.I):
            self.V('ref' + temp, "Vref" + temp, 0, self.__Vref)

    def _model_ivr_single_sc_feedback(self, count, output_pos, output_neg):
        temp = '_' + str(count)
        self.R('s1' + temp, 'VDD', '11' + temp, self.__Req1 / self.__alpha)
        self.C('p1' + temp, '11' + temp, 'VSS', self.__Ceq * self.__alpha)
        self.R('s2' + temp, '11' + temp, '12' + temp, self.__Req2 / self.__alpha)
        self.C('p2' + temp, '12' + temp, 'VSS', self.__Cout * self.__alpha)
        # self.R('p1', '12', 'VSS1', 1 / self.__alpha)
        self.CurrentControlledCurrentSource('s' + temp, '12' + temp, 'VSS', 'V_' + output_pos + '_' + output_neg,
                                            1 / self.__alpha)
        # self.CurrentControlledCurrentSource('s', '12', 'VSS', self.__Vnam, 1 / self.__alpha*12*12)
        self.R('g' + temp, 'VSS', output_neg, self.__Rg)
        # self.VoltageControlledVoltageSource('s', '13', 'VSS2', 'VDD1', 'VSS1', self.__alpha)
        self.B('s' + temp, '13' + temp, output_neg, v=self._alpha_expression(output_pos, output_neg, "Vref" + temp))
        self.R('s3' + temp, '13' + temp, '14' + temp, self.__Req1)
        self.C('p3' + temp, '14' + temp, output_neg, self.__Ceq)
        self.R('s4' + temp, '14' + temp, output_pos, self.__Req2)
        self.C('p4' + temp, output_pos, output_neg, self.__Cout)
        if re.match('Internal', self.__Vref_flag, re.I):
            self.V('ref' + temp, "Vref" + temp, 0, self.__Vref)

    def _alpha_expression(self, Vfbp, Vfbn, Vref):
        # expr = a*Vin+k*Vin*(Vref-Vfb)
        vin = self._get_voltage('VDD', 'VSS')
        vfb = self._get_voltage(Vfbp, Vfbn)
        vref = self._get_voltage(Vref)
        temp1 = self.expr_minus(vref, vfb)
        temp2 = self.expr_times(temp1, self.value2str(self.__k))
        temp3 = self.expr_add(self.value2str(self.__alpha), temp2)
        temp4 = self.conditional_operator(temp3 + '<1', self.conditional_operator(temp3 + '>0', temp3, '0'), '1')
        alpha = self.expr_times(temp4, vin)
        # return  self.conditional_operator(alpha+'<1',self.conditional_operator(alpha+'>0',alpha,'0'),'1')
        return alpha

    def _model_ivr_multiple(self):
        count = 0
        c4_nodes = self._nodes_pool_c4_inout(mode=1)
        for nodes in c4_nodes:
            count += 1
            if re.match('Yes', self.__Ivr_feedback_flag, re.I):
                if re.match('SC', self.__Ivr_type, re.I):
                    self._model_ivr_single_sc_feedback(count, nodes[0], nodes[1])
                elif re.match('Buck', self.__Ivr_type, re.I):
                    self._model_ivr_single_buck_feedback(count, nodes[0], nodes[1])
            else:
                self._model_ivr_sc_single(count, nodes[0], nodes[1])

    def _implement_die_grid(self, i, j, flag='None'):
        if re.match("Vertical", flag, re.I):
            a = i
            b = j + 1
        elif re.match("Horizontal", flag, re.I):
            a = i + 1
            b = j
        else:
            a = 0
            b = 0
            exit("Wrong flag! Choose from Vertical or Horizontal")

        # VDD
        node_temp_10 = self._pos2nodes(self.__nodes_power_grid[0][i], self.__nodes_power_grid[1][j], flag='VDD')
        node_temp_15 = self._pos2nodes((self.__nodes_power_grid[0][i] + self.__nodes_power_grid[0][a]) / 2,
                                       (self.__nodes_power_grid[1][j] + self.__nodes_power_grid[1][b]) / 2, flag='VDD')
        node_temp_20 = self._pos2nodes(self.__nodes_power_grid[0][a], self.__nodes_power_grid[1][b], flag='VDD')
        name_temp = '_' + node_temp_10 + '_' + node_temp_20
        self.R(name_temp, node_temp_10, node_temp_15, self.__Rdie)
        self.L(name_temp, node_temp_15, node_temp_20, self.__Ldie)

        # VSS
        node_temp_10 = self._pos2nodes(self.__nodes_power_grid[0][i], self.__nodes_power_grid[1][j], flag='VSS')
        node_temp_15 = self._pos2nodes((self.__nodes_power_grid[0][i] + self.__nodes_power_grid[0][a]) / 2,
                                       (self.__nodes_power_grid[1][j] + self.__nodes_power_grid[1][b]) / 2, flag='VSS')
        node_temp_20 = self._pos2nodes(self.__nodes_power_grid[0][a], self.__nodes_power_grid[1][b], flag='VSS')
        name_temp = '_' + node_temp_10 + '_' + node_temp_20
        self.R(name_temp, node_temp_10, node_temp_15, self.__Rdie)
        self.L(name_temp, node_temp_15, node_temp_20, self.__Ldie)

    def _implement_die_cap(self, i, j):
        node_temp_10 = self._pos2nodes(self.__nodes_power_grid[0][i], self.__nodes_power_grid[1][j], flag='VDD')
        node_temp_20 = self._pos2nodes(self.__nodes_power_grid[0][i], self.__nodes_power_grid[1][j], flag='VSS')
        name_temp = '_' + node_temp_10 + '_' + node_temp_20
        self.C(name_temp, node_temp_10, node_temp_20, self.__Cdie)

    def _implement_die_load(self, i, j, load_flag=1):
        node_temp_10 = self._pos2nodes(self.__nodes_power_grid[0][i - 1], self.__nodes_power_grid[1][j - 1], flag='VDD')
        node_temp_20 = self._pos2nodes(self.__nodes_power_grid[0][i - 1], self.__nodes_power_grid[1][j - 1], flag='VSS')
        name_temp = '_' + node_temp_10 + '_' + node_temp_20
        # Ngspice Manual: A current source of positive value forces current to flow out of the n+ node,
        # through the source, and into the n- node.
        if load_flag == 1:
            self.I(name_temp, node_temp_10, node_temp_10 + 'DM', 0.8, AC=1)
            self.V(name_temp, node_temp_10 + 'DM', node_temp_20,
                   0)  # it is used to sense the current so that support CCCS.
        else:
            self.I(name_temp, node_temp_10, node_temp_10 + 'DM', 0.8, AC=0)
            self.V(name_temp, node_temp_10 + 'DM', node_temp_20,
                   0)  # it is used to sense the current so that support CCCS.

    def _implement_die_load_res(self, i, j):
        node_temp_10 = self._pos2nodes(self.__nodes_power_grid[0][i - 1], self.__nodes_power_grid[1][j - 1], flag='VDD')
        node_temp_20 = self._pos2nodes(self.__nodes_power_grid[0][i - 1], self.__nodes_power_grid[1][j - 1], flag='VSS')
        name_temp = '_' + node_temp_10 + '_' + node_temp_20
        # Ngspice Manual: A current source of positive value forces current to flow out of the n+ node,
        # through the source, and into the n- node.
        self.R(name_temp, node_temp_10, node_temp_10 + 'DM', 1000)
        self.V(name_temp, node_temp_10 + 'DM', node_temp_20, 0)  # it is used to sense the current so that support CCCS.

    def _nodes_pool_c4_inout(self, mode=0):  # 0 for tuple and 1 for distributed IVR.
        temp = []
        for j in range(len(self.__nodes_c4_vdd[1])):  # Y
            for i in range(len(self.__nodes_c4_vdd[0])):  # X
                temp2 = self._pos2nodes(self.__nodes_c4_vdd[0][i], self.__nodes_c4_vdd[1][j], 'VDD')
                temp3 = self._pos2nodes(self.__nodes_c4_vss[0][i], self.__nodes_c4_vss[1][j], 'VSS')
                if mode == 0:
                    temp.append(temp2)
                    temp.append(temp3)
                else:
                    temp.append([temp2, temp3])
        return temp

    def nodes_pool_grid(self):
        temp = []
        for j in range(len(self.__nodes_power_grid[1])):  # Y
            for i in range(len(self.__nodes_power_grid[0])):  # X
                temp1 = self._name + '.' + self._pos2nodes(self.__nodes_power_grid[0][i], self.__nodes_power_grid[1][j],
                                                           'None')
                temp2 = self._name + '.' + self._pos2nodes(self.__nodes_power_grid[0][i], self.__nodes_power_grid[1][j],
                                                           'VDD')
                temp3 = self._name + '.' + self._pos2nodes(self.__nodes_power_grid[0][i], self.__nodes_power_grid[1][j],
                                                           'VSS')
                temp.append([temp1, temp2, temp3])
        return temp

    def nodes_pool_c4(self):  # something wrong with this function?
        temp = []
        for j in range(len(self.nodes_c4_vdd[1])):  # Y
            for i in range(len(self.nodes_c4_vdd[0])):  # X
                temp1 = self._name + '.' + 'bump' + '.' + self._pos2nodes(self.__nodes_c4_vdd[0][i],
                                                                          self.__nodes_c4_vdd[1][j],
                                                                          'None') + self._pos2nodes(
                    self.__nodes_c4_vss[0][i],
                    self.__nodes_c4_vss[1][j], 'None')
                temp2 = self._name + '.' + self._pos2nodes(self.__nodes_c4_vdd[0][i], self.__nodes_c4_vdd[1][j], 'VDD')
                temp3 = self._name + '.' + self._pos2nodes(self.__nodes_c4_vss[0][i], self.__nodes_c4_vss[1][j], 'VSS')
                temp.append([temp1, temp2, temp3])
        return temp

    def nodes_pool_load(self):
        temp = []
        if self.__nodes_load:
            for node in self.__nodes_load:
                temp1 = self._name + '.' + 'load' + '.' + self._pos2nodes(self.__nodes_power_grid[0][node[0]],
                                                                          self.__nodes_power_grid[1][node[1]], 'None')
                temp2 = self._pos2nodes(self.__nodes_power_grid[0][node[0] - 1],
                                        self.__nodes_power_grid[1][node[1] - 1], flag='VDD')
                temp3 = self._pos2nodes(self.__nodes_power_grid[0][node[0] - 1],
                                        self.__nodes_power_grid[1][node[1] - 1], flag='VSS')
                temp.append([temp1, temp2, temp3])
        return temp

    def implement(self, pdn, br_flag="", *args, ):
        NODES = list(self.__NODES)
        for i in range(len(NODES)):
            NODES[i] = NODES[i] + str(pdn.nodes_count) + br_flag
        pdn.circuit.X(self.sub_name + str(pdn.nodes_count) + br_flag, self.sub_name, *tuple(NODES))
        self._append_nodes_pair(pdn, br_flag)

    @staticmethod
    def update_nodes_pool(pdn, nodes):
        pdn.nodes_pool.extend(nodes)

    @staticmethod
    def _pos2nodes(x, y, flag='None'):
        if re.match("VDD", flag, re.I):
            return 'X' + str(int(x)) + 'Y' + str(int(y)) + 'VDD'
        elif re.match("VSS", flag, re.I):
            return 'X' + str(int(x)) + 'Y' + str(int(y)) + 'VSS'
        elif re.match("None", flag, re.I):
            return 'X' + str(int(x)) + 'Y' + str(int(y))
        else:
            print("Wrong flag! Choose from VDD or VSS.")

    @staticmethod
    def _get_voltage(pos, neg=None):
        if neg is None:
            return 'v(' + pos + ')'
        else:
            return 'v(' + pos + ',' + neg + ')'

    @staticmethod
    def value2str(num):
        return str(float(num))

    @staticmethod
    def expr_times(a, b):
        return '(' + a + '*' + b + ')'

    @staticmethod
    def expr_add(a, b):
        return '(' + a + '+' + b + ')'

    @staticmethod
    def expr_minus(a, b):
        return '(' + a + '-' + b + ')'

    @staticmethod
    def conditional_operator(a, b, c):
        return '(' + a + '?' + b + ':' + c + ')'


class ChipIVR(SubCircuit, Block4Ports):
    DEFAULT_NAME = "IntegratedVoltageRegulator"

    def __init__(self, pdn, name=None):
        if name is not None:
            self.sub_name = name
        else:
            self.sub_name = self.DEFAULT_NAME
        SubCircuit.__init__(self, self.sub_name, *self.NODES)
        self._model()
        pdn.circuit.subcircuit(self)

    def _model(self):
        print("Undefined PCB Voltage Regulator Model")


class ChipIVRBuck(ChipIVR):
    __Req1 = 0.018 @ u_Ohm
    __Req2 = 0.018 @ u_Ohm
    __alpha = 1 / 3
    __Ceq = 394 @ u_nF
    __Cout = 320 @ u_nF
    __Rg = 0.025 @ u_Ohm

    def __init__(self, pdn, name=None, **kwargs):
        self.set_parameter(**kwargs)
        super().__init__(pdn, name)

    def set_parameter(self, **kwargs):
        self.__Req1 = kwargs.get('Req1', self.__Req1)
        self.__Req2 = kwargs.get('Req2', self.__Req2)
        self.__alpha = kwargs.get('alpha', self.__alpha)
        self.__Ceq = kwargs.get('Ceq', self.__Ceq)
        self.__Cout = kwargs.get('Cout', self.__Cout)
        self.__Rg = kwargs.get('Rg', self.__Rg)

    def _model(self):
        self.R('s1', 'VDD1', '11', self.__Req1 / self.__alpha)
        self.C('p1', '11', 'VSS1', self.__Ceq * self.__alpha)
        self.R('s2', '11', '12', self.__Req2 / self.__alpha)
        self.C('p2', '12', 'VSS1', self.__Cout * self.__alpha)
        # self.R('p1', '12', 'VSS1', 1 / self.__alpha)
        self.V('sense', 's_pos', 's_neg', 0)
        self.CurrentControlledCurrentSource('s', '12', 'VSS1', 'vsense', 1 / self.__alpha)
        self.R('g', 'VSS1', 'VSS2', self.__Rg)
        self.VoltageControlledVoltageSource('s', '13', 'VSS2', 'VDD1', 'VSS1', self.__alpha)
        self.R('s3', '13', '14', self.__Req1)
        self.C('p3', '14', 'VSS2', self.__Ceq)
        self.R('s4', '14', 'VDD2', self.__Req2)
        self.C('p4', 'VDD2', 'VSS2', self.__Cout)

    def implement(self, pdn, br_flag=""):
        super().implement(pdn, br_flag)


class ChipIVRBuckWithFeedback(ChipIVR):
    __Req1 = 0.018 @ u_Ohm
    __Req2 = 0.018 @ u_Ohm
    __alpha = 1 / 3
    __Ceq = 394 @ u_nF
    __Cout = 320 @ u_nF
    __Rg = 0.025 @ u_Ohm
    __Vref = 1.1 @ u_V
    __k = 1
    __Vfbp = None
    __Vfbn = None

    def __init__(self, pdn, name=None, **kwargs):
        self.set_parameter(**kwargs)
        super().__init__(pdn, name)

    def set_parameter(self, **kwargs):
        self.__Req1 = kwargs.get('Req1', self.__Req1)
        self.__Req2 = kwargs.get('Req2', self.__Req2)
        self.__alpha = kwargs.get('alpha', self.__alpha)
        self.__Ceq = kwargs.get('Ceq', self.__Ceq)
        self.__Cout = kwargs.get('Cout', self.__Cout)
        self.__Rg = kwargs.get('Rg', self.__Rg)
        self.__Vref = kwargs.get('Vref', self.__Vref)
        self.__k = kwargs.get('k', self.__k)
        self.__Vfbp = kwargs.get('Vfbp', self.__Vfbp)
        self.__Vfbn = kwargs.get('Vfbn', self.__Vfbn)

    def _model(self):
        self.R('s1', 'VDD1', '11', self.__Req1 / self.__alpha)
        self.C('p1', '11', 'VSS1', self.__Ceq * self.__alpha)
        self.R('s2', '11', '12', self.__Req2 / self.__alpha)
        self.C('p2', '12', 'VSS1', self.__Cout * self.__alpha)
        # self.R('p1', '12', 'VSS1', 1 / self.__alpha)
        self.V('sense', 's_pos', 's_neg', 0)
        self.CurrentControlledCurrentSource('s', '12', 'VSS1', 'vsense', 1 / self.__alpha)
        self.R('g', 'VSS1', 'VSS2', self.__Rg)
        # self.VoltageControlledVoltageSource('s', '13', 'VSS2', 'VDD1', 'VSS1', self.__alpha)
        self.B('s', '13', 'VSS2', v=self.alpha_expression())
        self.R('s3', '13', '14', self.__Req1)
        self.C('p3', '14', 'VSS2', self.__Ceq)
        self.R('s4', '14', 'VDD2', self.__Req2)
        self.C('p4', 'VDD2', 'VSS2', self.__Cout)

    def implement(self, pdn, br_flag=""):
        super().implement(pdn, br_flag)

    def alpha_expression(self):
        # expr = a*Vin+k*Vin*(Vref-Vfb)
        vin = self.get_voltage('VDD1', 'VSS1')
        vfb = self.get_voltage(self.__Vfbp, self.__Vfbn)
        temp1 = self.expr_times(self.value2str(self.__alpha), vin)
        temp2 = self.expr_times(self.value2str(self.__k), vin)
        temp3 = self.expr_minus(self.value2str(self.__Vref), vfb)
        return self.expr_add(temp1, self.expr_times(temp2, temp3))

    @staticmethod
    def get_voltage(pos, neg=None):
        if neg is None:
            return 'v(' + pos + ')'
        else:
            return 'v(' + pos + ',' + neg + ')'

    @staticmethod
    def value2str(num):
        return str(float(num))

    @staticmethod
    def expr_times(a, b):
        return a + '*' + b

    @staticmethod
    def expr_add(a, b):
        return a + '+' + b

    @staticmethod
    def expr_minus(a, b):
        return a + '-' + b


class ChipPackage(SubCircuit, Block4Ports):
    DEFAULT_NAME = 'ChipPackage'

    __Rppkg = 0.5415 @ u_mOhm
    __Rspkg = 1 @ u_mOhm
    __Lppkg = 5.61 @ u_nH
    __Lspkg = 120 @ u_nH
    __Cppkg = 26 @ u_uF

    def __init__(self, pdn, name=None, **kwargs):
        if name is not None:
            self.sub_name = name
        else:
            self.sub_name = self.DEFAULT_NAME
        self.set_parameter(**kwargs)
        SubCircuit.__init__(self, self.sub_name, *self.NODES)
        self._model()
        pdn.circuit.subcircuit(self)

    def set_parameter(self, **kwargs):
        self.__Rppkg = kwargs.get('Rppkg', self.__Rppkg)
        self.__Rspkg = kwargs.get('Rspkg', self.__Rspkg)
        self.__Lspkg = kwargs.get('Lspkg', self.__Lspkg)
        self.__Lppkg = kwargs.get('Lppkg', self.__Lppkg)
        self.__Cppkg = kwargs.get('Cppkg', self.__Cppkg)

    def _model(self):

        # implement package
        self._implement_pkg_series(flag="VDD")
        self._implement_pkg_series(flag="VSS")
        self._implement_pkg_parallel(2)

    def _implement_pkg_series(self, flag="None"):
        if re.match("VDD", flag, re.I):
            temp = 'VDD'
        elif re.match("VSS", flag, re.I):
            temp = 'VSS'
        else:
            temp = 'None'
            exit("Wrong flag! Choose from VDD or VSS.")

        self.R("s" + temp, temp + '1', temp + "MS", self.__Rspkg)
        self.L("s" + temp, temp + "MS", temp + "2", self.__Lspkg)

    def _implement_pkg_parallel(self, node_num):
        temp_00 = "VDD" + str(node_num)
        temp_01 = temp_00 + "M"
        temp_10 = "VSS" + str(node_num)
        temp_11 = temp_10 + "M"
        self.R("p", temp_00, temp_01, self.__Rppkg)
        self.L("p", temp_10, temp_11, self.__Lppkg)
        self.C("p", temp_01, temp_11, self.__Cppkg)


class ChipBump(SubCircuit, Block4Ports):
    DEFAULT_NAME = 'ChipBump'

    __C4numX = 1
    __C4numY = 1
    __Rbump = 1 @ u_Ohm
    __Lbump = 1 @ u_H

    def __init__(self, pdn, name=None, **kwargs):
        if name is not None:
            self.sub_name = name
        else:
            self.sub_name = self.DEFAULT_NAME
        self.set_parameter(**kwargs)
        SubCircuit.__init__(self, self.sub_name, *self.NODES)
        self._model()
        pdn.circuit.subcircuit(self)

    def set_parameter(self, **kwargs):
        self.__C4numX = kwargs.get('C4numX', self.__C4numX)
        self.__C4numY = kwargs.get('C4numY', self.__C4numY)
        self.__Rbump = kwargs.get('Rbump', self.__Rbump)
        self.__Lbump = kwargs.get('Lbump', self.__Lbump)

    def _model(self):
        # implement C4 bumps
        for i in range(self.__C4numX):
            for j in range(self.__C4numY):
                node = 'X' + str(i) + 'Y' + str(j)
                node_vdd = node + self.GLOBAL_VDD
                node_vss = node + self.GLOBAL_VSS
                self.R(node_vdd, self.GLOBAL_VDD + '1', node_vdd + 'M', self.__Rbump)
                self.L(node_vdd, node_vdd + 'M', self.GLOBAL_VDD + "2", self.__Lbump)
                self.R(node_vss, self.GLOBAL_VSS + '1', node_vss + 'M', self.__Rbump)
                self.L(node_vss, node_vss + 'M', self.GLOBAL_VSS + "2", self.__Lbump)
