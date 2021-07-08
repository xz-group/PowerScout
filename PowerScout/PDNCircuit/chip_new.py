from PowerScout.PDNCircuit.Basic import *


class Core(SubCircuit, Block2Ports):
    DEFAULT_NAME = 'Core'

    # parameters for die
    __NODES = ()
    __Xstart = 1
    __Ystart = 1
    __Xstop = 3
    __Ystop = 3
    __Iload = [(2, 2)]
    __Iload_Flag = "All"
    __Rdie = 50 @ u_mOhm
    __Ldie = 5.6e-6 @ u_nH
    __Cdie = 0.12 @ u_nF

    # parameters for connection layer
    __C4numX = 1
    __C4numY = 1
    __C4shift = 0

    # parameters for IVR
    __Ivr_flag = 'No'
    __Ivr_feedback_flag = 'No'
    __Req1 = 0.018 @ u_Ohm
    __Req2 = 0.018 @ u_Ohm
    __alpha = 1 / 3
    __Ceq = 394 @ u_nF
    __Cout = 320 @ u_nF
    __Rg = 0.025 @ u_Ohm
    __Vref_flag = 'Internal'
    __Vref = 1.1 @ u_V
    __k = 1

    # temp variables
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

    def set_parameter_ivr(self, **kwargs):
        self.__Req1 = kwargs.get('Req1', self.__Req1)
        self.__Req2 = kwargs.get('Req2', self.__Req2)
        self.__alpha = kwargs.get('alpha', self.__alpha)
        self.__Ceq = kwargs.get('Ceq', self.__Ceq)
        self.__Cout = kwargs.get('Cout', self.__Cout)
        self.__Rg = kwargs.get('Rg', self.__Rg)
        self.__Vref = kwargs.get('Vref', self.__Vref)
        self.__k = kwargs.get('k', self.__k)
        self.__Ivr_feedback_flag = kwargs.get('IVRFb', self.__Ivr_feedback_flag)

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
        if re.match("Yes", self.__Iload_Flag, re.I):
            for node in self.__nodes_load:
                self._implement_die_load(node[0], node[1])
        elif re.match("No", self.__Iload_Flag, re.I):
            self.__nodes_load = []
        elif re.match("All", self.__Iload_Flag, re.I):
            for i in range(len(self.__nodes_power_grid[0])):  # X
                for j in range(len(self.__nodes_power_grid[1])):  # Y
                    self._implement_die_load(i, j)
                    self.__nodes_load.append((i, j))
        else:
            exit("Wrong Iload Flag! Choose from Yes or No")

    def _model_ivr_single(self, count, output_pos, output_neg):
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

    def _model_ivr_single_feedback(self, count, output_pos, output_neg):
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
        temp1 = self.expr_times(self.value2str(self.__alpha), vin)
        temp2 = self.expr_times(self.value2str(self.__k), vin)
        temp3 = self.expr_minus(vref, vfb)
        return self.expr_add(temp1, self.expr_times(temp2, temp3))

    def _model_ivr_multiple(self):
        count = 0
        c4_nodes = self._nodes_pool_c4_inout(mode=1)
        for nodes in c4_nodes:
            count += 1
            if re.match('Yes', self.__Ivr_feedback_flag, re.I):
                self._model_ivr_single_feedback(count, nodes[0], nodes[1])
            else:
                self._model_ivr_single(count, nodes[0], nodes[1])

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
        # Ngspice Manual: A current source of positive value forces current to flow out of the n+ node,
        # through the source, and into the n- node.
        self.I(name_temp, node_temp_10, node_temp_10 + 'DM', 0.01, AC=1)
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

    def implement(self, pdn, br_flag=""):
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
