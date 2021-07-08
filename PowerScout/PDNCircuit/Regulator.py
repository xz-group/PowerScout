###############################################################################
# This class defines the general form of the pcb level amp regulator
###############################################################################
from PowerScout.PDNCircuit.Basic import *


class PcbRegulator(SubCircuit, Block2Ports):
    DEFAULT_NAME = "Regulator"

    def __init__(self, pdn, name=None, **kwargs):
        if name is not None:
            self.sub_name = name
        else:
            self.sub_name = self.DEFAULT_NAME
        self.set_parameter(**kwargs)
        SubCircuit.__init__(self, self.sub_name, *self.NODES)
        self._model()
        pdn.circuit.subcircuit(self)

    def _model(self):
        print("Undefined PCB Voltage Regulator Model")

    def set_parameter(self, **kwargs):
        pass


class PcbRegulatorBi(SubCircuit, Block4Ports):
    DEFAULT_NAME = "RegulatorBi"

    def __init__(self, pdn, name=None, **kwargs):
        if name is not None:
            self.sub_name = name
        else:
            self.sub_name = self.DEFAULT_NAME
        self.set_parameter(**kwargs)
        SubCircuit.__init__(self, self.sub_name, *self.NODES)
        self._model()
        pdn.circuit.subcircuit(self)

    def _model(self):
        print("Undefined PCB Voltage Regulator Model")

    def set_parameter(self, **kwargs):
        pass


class PcbRegulatorIdeal(PcbRegulator):

    def __init__(self, pdn, name=None, amp=1.1, ac=0, current_flag=0):
        self.amp = amp
        self.ac = ac
        self.current_flag = current_flag
        super().__init__(pdn, name)

    def _model(self):
        if self.current_flag == 0:
            if self.ac == 0:
                self.V("s", "VDD", "VSS", self.amp)
            else:
                self.V("s", "VDD", "VSS", self.amp, AC=self.ac)
        else:
            if self.ac == 0:
                self.I("s", "VDD", "VSS", self.amp)
            else:
                self.I("s", "VDD", "VSS", self.amp, AC=self.ac)

    def implement(self, pdn, br_flag=""):
        super().implement(pdn, br_flag)
        pdn.circuit.R('gnd', self.GLOBAL_VSS + str(pdn.nodes_count) + br_flag, pdn.circuit.gnd, 0)


class PcbProbeAC(PcbRegulator):

    def __init__(self, pdn, name='ProbeAC', amp=1, ac=1, current_flag=1):
        self.amp = amp
        self.ac = ac
        self.current_flag = current_flag
        super().__init__(pdn, name)

    def _model(self):
        if self.current_flag == 1:
            self.I("s", "VDD", "VSS", self.amp, AC=self.ac)
        else:
            self.V("s", "VDD", "VSS", self.amp, AC=self.ac)

    def implement(self, pdn, br_flag=""):
        super().implement(pdn, br_flag)

    def implement_ground(self, pdn, br_flag=""):
        super().implement(pdn, br_flag)
        pdn.circuit.R('gnd', self.GLOBAL_VSS + str(pdn.nodes_count) + br_flag, pdn.circuit.gnd, 0)


class PcbLdoLT3083(PcbRegulatorBi):
    DEFAULT_NAME = 'PcbLdoLT3083'

    __Rout = 40 @ u_mOhm
    __Cout = 7.73 @ u_uF
    __Vin = 3.3 @ u_V
    __Vout = 1.2 @ u_V
    __fo1 = 1e3 @ u_Hz
    __fo2 = 1e7 @ u_Hz
    __PSRRlf = -90  # dB
    __PSRRhf = 0  # dB

    def __init__(self, pdn, name=None, **kwargs):
        super().__init__(pdn, name, **kwargs)

    def _model(self):
        self.CCCS('in', 'VDD1', 'VSS1', 'Vsense', float(self.__Vout / self.__Vin))
        self.C('in', 'VDD1', '32', self.__Cout)
        self.R('ines', '32', '33', 4.79 @ u_mOhm)
        self.L('ines', '33', 'VSS1', 3.29e-10)
        self.R('g', 'VSS1', 'VSS2', 0)
        self.V('out', '11', '12', self.__Vout)
        self.V('sense', '12', 'VSS2', 0)
        self.R('outhf', '11', '21', self.__Rout)
        self.R('outlf', '11', '11M', 1.34 @ u_mOhm)
        self.L('out', '11M', '21', 100 @ u_nH)
        self.C('out', '21', '22', self.__Cout)
        self.R('outes', '22', '23', 4.79 @ u_mOhm)
        self.L('outes', '23', '24', 3.29e-10)
        self.L('outm', '24', 'VSS2', 2e-9)
        self.R('min', '21', '21M', 1000 @ u_Ohm)
        self.L('minm', '21M', 'VSS2', 2e-9)
        self.B('ripple', 'VDD2', '21', v=self.expression())

    def set_parameter(self, **kwargs):
        self.__Rout = kwargs.get('Rout', self.__Rout)
        self.__Cout = kwargs.get('Cout', self.__Cout)
        self.__Vin = kwargs.get('Vin', self.__Vin)
        self.__Vout = kwargs.get('Vout', self.__Vout)
        self.__fo1 = kwargs.get('fo1', self.__fo1)
        self.__fo2 = kwargs.get('fo2', self.__fo2)
        self.__PSRRlf = kwargs.get('PSRRlf', self.__PSRRlf)
        self.__PSRRhf = kwargs.get('PSRRhf', self.__PSRRhf)

    def expression(self):
        freq = 'HERTZ'
        a1 = freq + '<' + str(float(self.__fo1))
        b1 = '(V(VDD1,VSS1)-' + str(float(self.__Vin)) + ')*' + self.db2linear_str(self.__PSRRlf)
        a2 = freq + '>' + str(float(self.__fo2))
        b2 = '(V(VDD1,VSS1)-' + str(float(self.__Vin)) + ')*' + self.db2linear_str(self.__PSRRhf)
        step = (self.__PSRRhf - self.__PSRRlf) / log(self.__fo2 / self.__fo1, 10)
        c2 = b1 + '*pow(' + freq + '/' + str(float(self.__fo1)) + ',' + str(step / 20) + ')'
        return self.conditional_operator(a1, b1, self.conditional_operator(a2, b2, c2))

    @staticmethod
    def conditional_operator(a, b, c):
        return a + '?' + b + ':' + c

    @staticmethod
    def db2linear_str(db):
        return str(pow(10, db / 20))


class PcbLdoMCP1726(PcbRegulatorBi):
    DEFAULT_NAME = 'PcbLdoMCP1726'

    __Rout = 200 @ u_mOhm
    __Cout = 3.39 @ u_uF
    __Vin = 3.3 @ u_V
    __Vout = 1.2 @ u_V
    __fo1 = 1e2 @ u_Hz
    __fo2 = 1e5 @ u_Hz
    __PSRRlf = -60  # dB
    __PSRRhf = 0  # dB

    def __init__(self, pdn, name=None, **kwargs):
        super().__init__(pdn, name, **kwargs)

    def _model(self):
        self.CCCS('in', 'VDD1', 'VSS1', 'Vsense', float(self.__Vout / self.__Vin))
        self.C('in', 'VDD1', '32', self.__Cout)
        self.R('ines', '32', '33', 5.36 @ u_mOhm)
        self.L('ines', '33', 'VSS1', 3.12e-10)
        self.R('g', 'VSS1', 'VSS2', 0)
        self.V('out', '11', '12', self.__Vout)
        self.V('sense', '12', 'VSS2', 0)
        self.R('outhf', '11', '21', self.__Rout)
        self.R('outlf', '11', '11M', 18 @ u_mOhm)
        self.L('out', '11M', '21', 200 @ u_nH)
        self.C('out', '21', '22', self.__Cout)
        self.R('outes', '22', '23', 5.36 @ u_mOhm)
        self.L('outes', '23', '24', 3.12e-10)
        self.L('outm', '24', 'VSS2', 2e-9)
        self.B('ripple', 'VDD2', '21', v=self.expression())

    def set_parameter(self, **kwargs):
        self.__Rout = kwargs.get('Rout', self.__Rout)
        self.__Cout = kwargs.get('Cout', self.__Cout)
        self.__Vin = kwargs.get('Vin', self.__Vin)
        self.__Vout = kwargs.get('Vout', self.__Vout)
        self.__fo1 = kwargs.get('fo1', self.__fo1)
        self.__fo2 = kwargs.get('fo2', self.__fo2)
        self.__PSRRlf = kwargs.get('PSRRlf', self.__PSRRlf)
        self.__PSRRhf = kwargs.get('PSRRhf', self.__PSRRhf)

    def expression(self):
        freq = 'HERTZ'
        a1 = freq + '<' + str(float(self.__fo1))
        b1 = '(V(VDD1,VSS1)-' + str(float(self.__Vin)) + ')*' + self.db2linear_str(self.__PSRRlf)
        a2 = freq + '>' + str(float(self.__fo2))
        b2 = '(V(VDD1,VSS1)-' + str(float(self.__Vin)) + ')*' + self.db2linear_str(self.__PSRRhf)
        step = (self.__PSRRhf - self.__PSRRlf) / log(self.__fo2 / self.__fo1, 10)
        c2 = b1 + '*pow(' + freq + '/' + str(float(self.__fo1)) + ',' + str(step / 20) + ')'
        return self.conditional_operator(a1, b1, self.conditional_operator(a2, b2, c2))

    @staticmethod
    def conditional_operator(a, b, c):
        return a + '?' + b + ':' + c

    @staticmethod
    def db2linear_str(db):
        return str(pow(10, db / 20))


class PcbBuckConverter(PcbRegulator):
    DEFAULT_NAME = 'PcbBuckConverter'

    # todo: 增加可以通过kwargs设置多个decouple电容
    def __init__(self, pdn, name=None, is_zero_ground=True, *, voltage, res_s, ind_s, cap_p, res_p, ind_p, **kwargs):
        self.__Cp = cap_p
        self.__Lp = ind_p
        self.__Rp = res_p
        self.__Ls = ind_s
        self.__Rs = res_s
        self.__Vs = voltage
        self.__is_zero_ground = is_zero_ground
        super().__init__(pdn, name, **kwargs)

    def _model(self):
        self.L('svdd', 'VDD', '31', self.__Ls)
        self.R('svdd', '31', '32', self.__Rs)
        self.V("s", "32", "33", self.__Vs)
        if self.__is_zero_ground:
            self.R('svss', '33', '34', 0)
            self.L('svss', 'VSS', '34', 0)
        else:
            self.R('svss', '33', '34', self.__Rs)
            self.L('svss', 'VSS', '34', self.__Ls)
        self.C('p', 'VDD', '12', self.__Cp)
        self.R('p', '12', '13', self.__Rp)
        self.L('p', '13', 'VSS', self.__Lp)

    def implement(self, pdn, br_flag=""):
        super().implement(pdn, br_flag)
        pdn.circuit.R('gnd', self.GLOBAL_VSS + str(pdn.nodes_count) + br_flag, pdn.circuit.gnd, 0)


class PcbVoltageRegulatorSimple(PcbRegulator):
    def __init__(self, pdn, name=None, *, voltage, res_s, ind_s, **kwargs):
        self.__Ls = ind_s
        self.__Rs = res_s
        self.__Vs = voltage
        super().__init__(pdn, name, **kwargs)

    def _model(self):
        self.L('svdd', 'VDD', '31', self.__Ls)
        self.R('svdd', '31', '32', self.__Rs)
        self.V("s", "32", "VSS", self.__Vs)

    def implement(self, pdn, br_flag=""):
        super().implement(pdn, br_flag)
        pdn.circuit.R('gnd', self.GLOBAL_VSS + str(pdn.nodes_count) + br_flag, pdn.circuit.gnd, 0)


class PcbBuckConverter2(PcbRegulator):
    DEFAULT_NAME = 'PcbBuckConverter'
    __C1 = 910 @ u_uF
    __L1 = 14.1 @ u_nH
    __R1 = 0.006 @ u_Ohm
    __C2 = 34.3 @ u_uF
    __L2 = 5.5 @ u_nH
    __R2 = 0.005 @ u_Ohm
    __Ls = 100 @ u_nH
    __Rs = 3 @ u_mOhm
    __Vs = 1.1

    def __init__(self, pdn, name=None, **kwargs):
        super().__init__(pdn, name, **kwargs)

    def _model(self):
        self.C('1', 'VDD', '12', self.__C1)
        self.R('1', '12', '13', self.__R1)
        self.L('1', '13', 'VSS', self.__L1)
        self.C('2', 'VDD', '22', self.__C2)
        self.R('2', '22', '23', self.__R2)
        self.L('2', '23', 'VSS', self.__L2)
        self.L('s', 'VDD', '31', self.__Ls)
        self.R('s', '31', '32', self.__Rs)
        self.V("s", "32", "VSS", self.__Vs)

    def implement(self, pdn, br_flag=""):
        super().implement(pdn, br_flag)
        pdn.circuit.R('gnd', self.GLOBAL_VSS + str(pdn.nodes_count) + br_flag, pdn.circuit.gnd, 0)

    def set_parameter(self, **kwargs):
        self.__C1 = kwargs.get('C1', self.__C1)
        self.__L1 = kwargs.get('L1', self.__L1)
        self.__R1 = kwargs.get('R1', self.__R1)
        self.__C2 = kwargs.get('C2', self.__C2)
        self.__L2 = kwargs.get('L2', self.__L2)
        self.__R2 = kwargs.get('R2', self.__R2)
        self.__Ls = kwargs.get('Ls', self.__Ls)
        self.__Rs = kwargs.get('Rs', self.__Rs)
        self.__Vs = kwargs.get('Vs', self.__Vs)
