import os
import re
import time
from PySpice1v5.Spice.Netlist import SubCircuit, Circuit
from PySpice1v5.Unit import *
import PySpice1v5.Logging.Logging as Logging

logger = Logging.setup_logging(logging_level='CRITICAL')


class Global:
    GLOBAL_VDD = 'VDD'
    GLOBAL_VSS = 'VSS'

    @staticmethod
    def _brunch2count(pdn):
        pdn.nodes_count = pdn.nodes_brunch

    @staticmethod
    def _add_nodes_count(pdn):
        pdn.nodes_count += 1

    def _append_nodes_pair(self, pdn, br_flag="", node_type='Voltage'):
        if node_type == 'Voltage':
            pdn.nodes_pool.append(
                ['V' + str(pdn.nodes_count) + br_flag,
                 self.GLOBAL_VDD + str(pdn.nodes_count) + br_flag,
                 self.GLOBAL_VSS + str(pdn.nodes_count) + br_flag])


class PowerDeliveryNetwork(Global):
    def __init__(self, title=None):
        if title is None:
            time_stamp = time.strftime('%Y%m%d-%H%M%S', time.localtime(time.time()))
            self.circuit = Circuit(time_stamp)
        else:
            self.circuit = Circuit(title)

        self.brunch_flag = ['']
        self.cap_temp = {}
        self.nodes_count = 0
        self.nodes_brunch = 0
        self.nodes_pool = []
        self.freq = []

        self._parameters()
        self._components()
        self._structure()

    def _components(self):
        pass

    def _parameters(self):
        pass

    def _structure(self):
        pass

    def simulate(self):
        pass

    def print(self):
        print(self.circuit)

    def plot(self):
        pass


class Block4Ports(Global):
    NODES = ('VDD1', 'VSS1', 'VDD2', 'VSS2')

    def __init__(self):
        self.sub_name = ""

    def implement(self, pdn, br_flag=""):
        pdn.circuit.X(self.sub_name + str(pdn.nodes_count) + br_flag, self.sub_name,
                      self.GLOBAL_VDD + str(pdn.nodes_count) + br_flag,
                      self.GLOBAL_VSS + str(pdn.nodes_count) + br_flag,
                      self.GLOBAL_VDD + str(pdn.nodes_count + 1) + br_flag,
                      self.GLOBAL_VSS + str(pdn.nodes_count + 1) + br_flag)
        self._add_nodes_count(pdn)
        self._append_nodes_pair(pdn, br_flag)


class Block2Ports(Global):
    NODES = ('VDD', 'VSS')

    def __init__(self):
        self.sub_name = ""

    def implement(self, pdn, br_flag="", name=None):
        if name is None:
            pdn.circuit.X(self.sub_name + str(pdn.nodes_count) + br_flag, self.sub_name,
                          self.GLOBAL_VDD + str(pdn.nodes_count) + br_flag,
                          self.GLOBAL_VSS + str(pdn.nodes_count) + br_flag)
        else:
            pdn.circuit.X(self.sub_name + str(pdn.nodes_count) + br_flag + name, self.sub_name,
                          self.GLOBAL_VDD + str(pdn.nodes_count) + br_flag,
                          self.GLOBAL_VSS + str(pdn.nodes_count) + br_flag)
        self._append_nodes_pair(pdn, br_flag)


class BasicCircuitRLC(SubCircuit, Block4Ports):
    DEFAULT_NAME = 'RLC_Circuit'

    def __init__(self, pdn, name=None, is_zero_ground=True, *, res_s, ind_s, cap_p, res_p, ind_p):
        if name is not None:
            self.sub_name = name
        else:
            self.sub_name = self.DEFAULT_NAME
        self.__Cp = cap_p
        self.__Lp = ind_p
        self.__Rp = res_p
        self.__Ls = ind_s
        self.__Rs = res_s
        self.__is_zero_ground = is_zero_ground
        SubCircuit.__init__(self, self.sub_name, *self.NODES)
        self._model()
        pdn.circuit.subcircuit(self)

    def _model(self):
        self.L('svdd', 'VDD1', '31', self.__Ls)
        self.R('svdd', '31', 'VDD2', self.__Rs)
        if self.__is_zero_ground:
            self.R('svss', 'VSS2', '34', 0)
            self.L('svss', 'VSS1', '34', 0)
        else:
            self.R('svss', 'VSS2', '34', self.__Rs)
            self.L('svss', 'VSS1', '34', self.__Ls)
        self.C('p', 'VDD2', '12', self.__Cp)
        self.R('p', '12', '13', self.__Rp)
        self.L('p', '13', 'VSS2', self.__Lp)


class PcbModelLumped(SubCircuit, Block4Ports):
    DEFAULT_NAME = 'PcbModelLumped'
    __Rs = 1000 @ u_mOhm
    __Ls = 0 @ u_nH
    __Rp = 0 @ u_mOhm
    __Cp = 0 @ u_uF
    __Lp = 0 @ u_nH

    def __init__(self, pdn, name=None, is_zero_ground=False, **kwargs):
        if name is not None:
            self.sub_name = name
        else:
            self.sub_name = self.DEFAULT_NAME
        self.is_zero_ground = is_zero_ground
        self.set_parameter(**kwargs)
        SubCircuit.__init__(self, self.sub_name, *self.NODES)
        self._model()
        pdn.circuit.subcircuit(self)

    def set_parameter(self, **kwargs):
        self.__Rs = kwargs.get('Rspcb', self.__Rs)
        self.__Ls = kwargs.get('Lspcb', self.__Ls)
        self.__Rp = kwargs.get('Rppcb', self.__Rp)
        self.__Cp = kwargs.get('Cppcb', self.__Cp)
        self.__Lp = kwargs.get('Lppcb', self.__Lp)

    def _model(self):
        self.R("s1", "VDD1", "11", self.__Rs)
        self.L("s1", "11", "VDD2", self.__Ls)

        if self.is_zero_ground:
            self.R("s2", "VSS1", "21", 0)
            self.L("s2", "21", "VSS2", 0)
        else:
            self.R("s2", "VSS1", "21", self.__Rs)
            self.L("s2", "21", "VSS2", self.__Ls)

        self.R("p", "VDD2", "31", self.__Rp)
        self.L('p', "31", "32", self.__Lp)
        self.C("p", "32", "VSS2", self.__Cp)


class PcbWireLine(SubCircuit, Block4Ports):
    DEFAULT_NAME = 'PcbWireLine'
    __Rs = 1 @ u_mOhm
    __Ls = 2 @ u_nH
    __zero_ground_flag = 'No'

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
        self.__zero_ground_flag = kwargs.get('GFlag', self.__zero_ground_flag)
        self.__Rs = kwargs.get('Rs', self.__Rs)
        self.__Ls = kwargs.get('Ls', self.__Ls)

    def _model(self):
        self.R("s1", "VDD1", "11", self.__Rs)
        self.L("s1", "11", "VDD2", self.__Ls)
        if re.match("No", self.__zero_ground_flag, re.I):
            self.L("s2", "21", "VSS2", self.__Ls)
            self.R("s2", "VSS1", "21", self.__Rs)
        else:
            self.R("s2", "VSS1", "VSS2", 0)

    def implement_length(self, pdn, br_flag="", length=1):
        for i in range(length):
            self.implement(pdn, br_flag)


class PcbCapacitorSimple(SubCircuit, Block2Ports):
    DEFAULT_NAME = 'PcbCapacitorSimple'
    __ESR = 1e9 @ u_Ohm
    __ESL = 0 @ u_H
    __C = 0 @ u_F
    __ESL_M = 2 @ u_nH

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
        self.__ESR = kwargs.get('R', self.__ESR)
        self.__ESL = kwargs.get('L', self.__ESL)
        self.__C = kwargs.get('C', self.__C)
        self.__ESL_M = kwargs.get('LM', self.__ESL_M)

    def _model(self):
        self.C("p", "VDD", "11", self.__C @ u_F)
        self.L("p", "11", "12", self.__ESL @ u_H)
        self.R("p", "12", "13", self.__ESR @ u_Ohm)
        self.L("m", "13", "VSS", self.__ESL_M @ u_nH)

    def implementN(self, pdn, br_flag="", name=None, number=1):
        if name is None:
            for i in range(number):
                self.implement(pdn, br_flag, name='C' + str(i))
        else:
            for i in range(number):
                self.implement(pdn, br_flag, name=name + str(i))


class PcbCapacitorSimpleList(Global):

    def __init__(self, pdn, cap_list, mode='Value_Number_Package', path=None, **pcb_kwargs):

        self.dict_cap = {}  # contains all the information of the capacitors
        self.pn_list = []  # contains the names and corresponding numbers
        self.capacitor_models = []  # contains the instances of the capacitors

        if mode is 'Value_Number_Package':
            self._generate_dict_list_value_number_package(cap_list, path)

        for cap in self.pn_list:
            self.capacitor_models.append(PcbCapacitorSimple(pdn, cap[0], **self.dict_cap[cap[0]]))

        self.wire_model = PcbWireLine(pdn, name=None, **pcb_kwargs)

    ######################################################################
    # This function finds out the PN of the capacitor according to the capacitance value.
    def _get_name_from_value_package(self, cap_lib, value, package=1):
        value = str(value)
        value = value.replace(' ', '')
        value = value.replace('μ', 'u')
        value = self._unit_tech2sci(value)
        name = []
        for model in cap_lib.keys():
            if cap_lib[model]['Value'] == value:
                name.append(model)
        if package > len(name):  # need to refine later
            return name[0]
        else:
            return name[package - 1]

    def _read_cap_models(self, file_path):
        if file_path is None:
            path = ".././capModel"
        else:
            path = file_path
        files = os.listdir(path)  # 得到文件夹下的所有文件名称
        cap_model = {}
        for file in files:  # 遍历文件夹
            if not os.path.isdir(file):  # 判断是否是文件夹，不是文件夹才打开
                f = open(path + "/" + file)  # 打开文件
                iter_f = iter(f)  # 创建迭代器
                temp_line = {}
                for line in iter_f:  # 遍历文件，一行行遍历，读取文本
                    if "Murata P/N" in line:
                        line = line.strip('\n')
                        temp = re.sub(" ", "", line)
                        temp_line.update(PN=re.sub(r".*:", "", temp))
                    if "Description" in line:
                        line = line.strip('\n')
                        temp = re.sub(" ", "", line)
                        temp = re.sub(r".*:", "", temp)
                        [size, temp_char, value, volt] = re.split("/", temp)
                        value = self._unit_tech2sci(value)
                        temp_line.update(Size=size, TempChar=temp_char, Value=value, Volt=volt)
                    if re.match("C ", line, re.I):
                        line = line.strip('\n')
                        temp = re.split(" ", line)[-1]
                        temp = float(temp)
                        temp_line.update(C=temp)

                    if re.match("L ", line, re.I):
                        line = line.strip('\n')
                        temp = re.split(" ", line)[-1]
                        temp = float(temp)
                        temp_line.update(L=temp)

                    if re.match("R ", line, re.I):
                        line = line.strip('\n')
                        temp = re.split(" ", line)[-1]
                        temp = float(temp)
                        temp_line.update(R=temp)

                cap_model[temp_line.get("PN")] = temp_line
        return cap_model

    @staticmethod
    def _unit_tech2sci(value_string):
        unit_tech = re.sub(r'[^A-Za-z]', '', value_string)
        digital = float(value_string.replace(unit_tech, ''))
        if re.match(unit_tech, 'fF', re.I):
            digital = digital * 1e-15
        elif re.match(unit_tech, 'pF', re.I):
            digital = digital * 1e-12
        elif re.match(unit_tech, 'nF', re.I):
            digital = digital * 1e-9
        elif re.match(unit_tech, 'uF', re.I):
            digital = digital * 1e-6
        else:
            pass
        return format(digital, '.5e')

    def _generate_dict_list_value_number_package(self, cap_list, path):
        dict_temp = self._read_cap_models(path)
        for cap in cap_list:
            pn = self._get_name_from_value_package(dict_temp, cap[0])
            self.pn_list.append([pn, cap[1]])
            self.dict_cap[pn] = dict_temp[pn]
            self.dict_cap[pn].update(Number=cap[1])

    def implement(self, pdn, br_flag='', interval=1):
        for i in range(len(self.capacitor_models)):
            for j in range(self.pn_list[i][1]):
                self.capacitor_models[i].implement(pdn, br_flag)
                self.wire_model.implement_length(pdn, br_flag, interval)


class PcbPlane(SubCircuit, Block2Ports):
    DEFAULT_NAME = 'PcbPlane'
    __ESR = 1.739 @ u_Ohm
    __ESC = 0.0065 @ u_F

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
        self.__ESR = kwargs.get('R', self.__ESR)
        self.__ESC = kwargs.get('C', self.__ESC)

    def _model(self):
        self.C("p", "VDD", "11", self.__ESC @ u_F)
        self.R("p", "11", "VSS", self.__ESR @ u_Ohm)


class PcbBranchNode1toN(SubCircuit, Block2Ports):
    DEFAULT_NAME = 'PcbBrunchNode'

    def __init__(self, pdn, name=None, number=2):
        if name is not None:
            self.sub_name = name + str(number)
        else:
            self.sub_name = self.DEFAULT_NAME + str(number)

        nodes = ['VDD', 'VSS']
        for i in range(number):
            pdn.brunch_flag.append(chr(i + 65))
            nodes.append("VDD" + str(i + 1))
            nodes.append("VSS" + str(i + 1))
        SubCircuit.__init__(self, self.sub_name, *tuple(nodes))
        self._model(number)
        pdn.circuit.subcircuit(self)

    def _model(self, number):
        for i in range(number):
            self.R('CN1' + str(i + 1), 'VDD', 'VDD' + str(i + 1), 0)
            self.R('CN2' + str(i + 1), 'VSS', 'VSS' + str(i + 1), 0)

    def implement(self, pdn, *args, br_flag=""):
        pdn.nodes_brunch = pdn.nodes_count
        temp = [self.GLOBAL_VDD + str(pdn.nodes_brunch), self.GLOBAL_VSS + str(pdn.nodes_brunch)]
        for i in range(len(pdn.brunch_flag) - 1):
            self._append_nodes_pair(pdn, pdn.brunch_flag[i + 1])
            temp.append(self.GLOBAL_VDD + str(pdn.nodes_brunch) + pdn.brunch_flag[i + 1])
            temp.append(self.GLOBAL_VSS + str(pdn.nodes_brunch) + pdn.brunch_flag[i + 1])
        temp_tuple = tuple(temp)
        pdn.circuit.X(self.sub_name, self.sub_name, *temp_tuple)
        return pdn.brunch_flag

    def implement2(self, pdn, a='', b='A', c='B'):
        pdn.nodes_brunch = pdn.nodes_count
        temp = [self.GLOBAL_VDD + str(pdn.nodes_brunch) + a, self.GLOBAL_VSS + str(pdn.nodes_brunch) + a]
        temp.append(self.GLOBAL_VDD + str(pdn.nodes_brunch) + b)
        temp.append(self.GLOBAL_VSS + str(pdn.nodes_brunch) + b)
        temp.append(self.GLOBAL_VDD + str(pdn.nodes_brunch) + c)
        temp.append(self.GLOBAL_VSS + str(pdn.nodes_brunch) + c)
        temp_tuple = tuple(temp)
        pdn.circuit.X(self.sub_name + str(pdn.nodes_brunch), self.sub_name, *temp_tuple)

    @staticmethod
    def change_brunch(pdn):
        pdn.nodes_count = pdn.nodes_brunch


class PcbSamplingResistor(SubCircuit, Block4Ports):
    DEFAULT_NAME = 'PcbSamplingResistor'

    def __init__(self, pdn, name=None, Rs=0):
        if name is not None:
            self.sub_name = name
        else:
            self.sub_name = self.DEFAULT_NAME
        SubCircuit.__init__(self, self.sub_name, *self.NODES)
        self._model(Rs)
        pdn.circuit.subcircuit(self)

    def _model(self, Rs):
        self.R("s1", "VDD1", "VDD1M", Rs)
        self.L("s1m", "VDD1M", "VDD2", 2 @ u_nH)
        # self.R("s2", "VSS1", "VSS2", Rs)
        self.R("s2", "VSS1", "VSS2", 0)


class AnalogGate_AND(SubCircuit, Block2Ports):
    DEFAULT_NAME = 'AND_Gate'

    def __init__(self, pdn, name=None, number=2, threshold=0.5):
        self.th = threshold
        self.num = number
        if name is not None:
            self.sub_name = name + str(number)
        else:
            self.sub_name = self.DEFAULT_NAME + str(number)

        nodes = ['OUTP', 'OUTN']
        for i in range(number):
            nodes.append("INP" + str(i + 1))
            nodes.append("INN" + str(i + 1))
        SubCircuit.__init__(self, self.sub_name, *tuple(nodes))
        self._model(number)
        pdn.circuit.subcircuit(self)

    def _model(self, number):
        self.B('and', 'OUTP', 'OUTN', v=self._expression(number))

    def implement(self, pdn, *args, br_flag="", name=None):
        if len(args) is 0:
            temp = ['OUTP' + br_flag, 'OUTN' + br_flag]
        else:
            temp = [args[0], args[1]]
        for i in range(self.num):
            temp.append('INP' + str(i + 1) + br_flag)
            temp.append('INN' + str(i + 1) + br_flag)
        temp_tuple = tuple(temp)
        if name is None:
            pdn.circuit.X(self.sub_name, self.sub_name, *temp_tuple)
        else:
            pdn.circuit.X(name, self.sub_name, *temp_tuple)
        return pdn.brunch_flag

    @staticmethod
    def _get_voltage(pos, neg=None):
        if neg is None:
            return 'v(' + pos + ')'
        else:
            return 'v(' + pos + ',' + neg + ')'

    @staticmethod
    def _value2str(num):
        return str(float(num))

    @staticmethod
    def _expr_lt(a, b):
        return '(' + a + '<' + b + ')'

    @staticmethod
    def _expr_gt(a, b):
        return '(' + a + '>' + b + ')'

    @staticmethod
    def _conditional_operator(a, b, c):
        return '(' + a + '?' + b + ':' + c + ')'

    def _analog_to_digital(self, pos, neg):
        return self._conditional_operator(self._expr_lt(self._get_voltage(pos, neg), self._value2str(self.th)),
                                          self._value2str(0), self._value2str(1))

    def _expression(self, number):
        temp = []
        for i in range(number):
            temp.append(self._analog_to_digital("INP" + str(i + 1), "INN" + str(i + 1)))
        print(temp)
        expr = temp[0]
        for i in range(number)[1:]:
            expr = expr + '&&' + temp[i]
        return expr


class PowerDeliveryNetworkFactory(PowerDeliveryNetwork):

    def __init__(self, title=None):
        super().__init__(title)
