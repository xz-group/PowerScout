import matplotlib.pyplot as plt
from Basic import PowerDeliveryNetworkFactory, PcbModelLumped
from Chip import ChipSingleCore, ChipLumped
from Regulator import PcbRegulatorIdeal, PcbProbeAC


class pdn2007date_distributed(PowerDeliveryNetworkFactory):
    """ built in pdn based on the 2007 date paper (distributed)

        Reference:
        Gupta, Meeta S., Jarod L. Oatley, Russ Joseph, Gu-Yeon Wei, and David M. Brooks.
        "Understanding voltage variations in chip multiprocessors using a distributed power-delivery network."
        In Proceedings of the conference on Design, automation and test in Europe, pp. 624-629. EDA Consortium, 2007.
    """

    def __init__(self, title):
        self.chipModel = {'name': 'chip', 'Xstop': 12, 'Ystop': 12, 'C4numX': 10, 'C4numY': 10, 'C4shift': 0,
                          'Cdie': 2.2 @ u_nF,
                          'Rdie': 50 @ u_mOhm, 'Ldie': 5.6e-6 @ u_nH, 'IFlag': 'All', 'Iload': [(5, 5)]}

        self.pkgModel = {'Rbump': 40 @ u_mOhm, 'Lbump': 72e-3 @ u_nH, 'Rppkg': 0.5415 @ u_mOhm, 'Rspkg': 1 @ u_mOhm,
                         'Lspkg': 120e-3 @ u_nH, 'Lppkg': 5.61e-3 @ u_nH, 'Cppkg': 26 @ u_uF}
        self.pcbModel = {'Rs': 0.094 @ u_mOhm, 'Ls': 21e-3 @ u_nH, 'Cp': 240 @ u_uF, 'Rp': 0.1666 @ u_mOhm}
        self.chipModel.update(self.pkgModel)
        PowerDeliveryNetworkFactory.__init__(self, title=title)

    def _structure(self):
        vr = PcbRegulatorIdeal(self, amp=1)
        pcb = PcbModelLumped(self, **self.pcbModel)
        chip = ChipSingleCore(self, **self.chipModel)
        vr.implement(self)
        pcb.implement(self)
        chip.implement(self)
        self.circuit.raw_spice = '.option rshunt = 1.0e12'

    def ac_simulate(self):
        self.simulator = self.circuit.simulator(temperature=25, nominal_temperature=25)
        self.analysis = self.simulator.ac(start_frequency=1e5, stop_frequency=1e9, number_of_points=100,
                                          variation='dec')

    def plot_impedance(self):
        impedance = abs(self.analysis['Xchip.X50Y50VDD'] - self.analysis.vss0)
        # impedance = abs(self.analysis['Xchip.X50Y50VDD'] - self.analysis['Xchip.X50Y50VSS'])
        freq = self.analysis.frequency
        plt.semilogx(freq, impedance)
        plt.xlim([1e5, 1e9])
        # plt.ylim([0, 9e-3])
        # plt.grid()


class Pdn2007DateLumped(PowerDeliveryNetworkFactory):
    """ built in pdn based on the 2007 date paper (lumped)

        Reference:
        Gupta, Meeta S., Jarod L. Oatley, Russ Joseph, Gu-Yeon Wei, and David M. Brooks.
        "Understanding voltage variations in chip multiprocessors using a distributed power-delivery network."
        In Proceedings of the conference on Design, automation and test in Europe, pp. 624-629. EDA Consortium, 2007.
    """

    def __init__(self, title, **kwargs):
        self.model = {}
        self.__chipModel = {'Cdie': 335 @ u_nF, 'Rdie': 0.1 @ u_mOhm, 'IFlag': 'Yes'}
        self.__pkgModel = {'Rbump': 0.3 @ u_mOhm, 'Lbump': 0.5e-3 @ u_nH, 'Rppkg': 0.5415 @ u_mOhm, 'Rspkg': 1 @ u_mOhm,
                           'Lspkg': 0.12 @ u_nH, 'Lppkg': 0.00561 @ u_nH, 'Cppkg': 26 @ u_uF}
        self.__pcbModel = {'Rspcb': 0.094 @ u_mOhm, 'Lspcb': 21e-3 @ u_nH, 'Cppcb': 240 @ u_uF,
                           'Rppcb': 0.1666 @ u_mOhm}
        self.model.update(self.__chipModel)
        self.model.update(self.__pkgModel)
        self.model.update(self.__pcbModel)
        self.model.update(**kwargs)
        PowerDeliveryNetworkFactory.__init__(self, title=title)

    def _structure(self):
        vr = PcbRegulatorIdeal(self, amp=1)
        pcb = PcbModelLumped(self, zero_path=False, **self.model)
        chip = ChipLumped(self, name='chip', **self.model)  # cannot put name in the dictionary.
        vr.implement(self)
        pcb.implement(self)
        chip.implement(self)
        # self.circuit.raw_spice = '.option rshunt = 1.0e12'

    def ac_simulate(self):
        self.simulator = self.circuit.simulator(temperature=25, nominal_temperature=25)
        self.analysis = self.simulator.ac(start_frequency=1e5, stop_frequency=1e9, number_of_points=100,
                                          variation='dec')

    def plot_impedance(self, label_para=None, label_other=None, reference=None):
        # impedance = abs(
        #     self.analysis['Xchip.dieVDD'] - self.analysis.vss0)  # use this to make the results the same as the paper
        impedance = abs(self.analysis['Xchip.diecapVDD'] - self.analysis['Xchip.diecapVSS'])
        freq = self.analysis.frequency
        if label_para is None and label_other is None:
            plt.semilogx(freq, impedance)
        elif label_para is not None:
            plt.semilogx(freq, impedance, label=label_para + ': ' + str(self.model.get(label_para)))
        else:
            plt.semilogx(freq, impedance, label=label_other)
        plt.xlim([1e5, 1e9])
        # plt.ylim([0, 9e-3])
        if reference is None:
            return impedance
        else:
            return impedance - reference

    def print_parameter_name(self):
        print(self.model.keys())
        return self.model.keys()


class Pdn2007DateLumped_OffChip(PowerDeliveryNetworkFactory):
    """ built in pdn based on the 2007 date paper (lumped,seen from off-chip point)

        Reference:
        Gupta, Meeta S., Jarod L. Oatley, Russ Joseph, Gu-Yeon Wei, and David M. Brooks.
        "Understanding voltage variations in chip multiprocessors using a distributed power-delivery network."
        In Proceedings of the conference on Design, automation and test in Europe, pp. 624-629. EDA Consortium, 2007.
    """

    def __init__(self, title, **kwargs):
        self.model = {}
        self.__chipModel = {'Cdie': 335 @ u_nF, 'Rdie': 0.1 @ u_mOhm, 'IFlag': 'No'}
        self.__pkgModel = {'Rbump': 0.3 @ u_mOhm, 'Lbump': 0.5e-3 @ u_nH, 'Rppkg': 0.5415 @ u_mOhm, 'Rspkg': 1 @ u_mOhm,
                           'Lspkg': 0.12 @ u_nH, 'Lppkg': 0.00561 @ u_nH, 'Cppkg': 26 @ u_uF}
        self.__pcbModel = {'Rspcb': 0.094 @ u_mOhm, 'Lspcb': 21e-3 @ u_nH, 'Cppcb': 240 @ u_uF,
                           'Rppcb': 0.1666 @ u_mOhm}
        self.model.update(self.__chipModel)
        self.model.update(self.__pkgModel)
        self.model.update(self.__pcbModel)
        self.model.update(**kwargs)
        PowerDeliveryNetworkFactory.__init__(self, title=title)

    def _structure(self):
        vr = PcbRegulatorIdeal(self, amp=1)
        pcb = PcbModelLumped(self, zero_path=False, **self.model)
        probe = PcbProbeAC(self)
        chip = ChipLumped(self, name='chip', **self.model)  # cannot put name in the dictionary.
        vr.implement(self)
        pcb.implement(self)
        probe.implement(self)
        chip.implement(self)
        # self.circuit.raw_spice = '.option rshunt = 1.0e12'

    def ac_simulate(self):
        self.simulator = self.circuit.simulator(temperature=25, nominal_temperature=25)
        self.analysis = self.simulator.ac(start_frequency=1e5, stop_frequency=1e9, number_of_points=100,
                                          variation='dec')

    def plot_impedance(self, label_para=None, label_other=None, reference=None):
        impedance = abs(self.analysis.vdd1 - self.analysis.vss1)
        # impedance = abs(self.analysis['Xchip.diecapVDD'] - self.analysis['Xchip.diecapVSS'])
        freq = self.analysis.frequency
        if label_para is None and label_other is None:
            pass
        elif label_para is not None:
            plt.semilogx(freq, impedance, label=label_para + ': ' + str(self.model.get(label_para)))
        else:
            plt.semilogx(freq, impedance, label=label_other)
        plt.xlim([1e5, 1e9])
        # plt.ylim([0, 9e-3])
        if reference is None:
            return impedance
        else:
            return impedance - reference

    def print_parameter_name(self):
        print(self.model.keys())
        return self.model.keys()


class Pdn2007DateLumped_Regulator(PowerDeliveryNetworkFactory):
    """ built in pdn based on the 2007 date paper (lumped,seen from regulator point)

        Reference:
        Gupta, Meeta S., Jarod L. Oatley, Russ Joseph, Gu-Yeon Wei, and David M. Brooks.
        "Understanding voltage variations in chip multiprocessors using a distributed power-delivery network."
        In Proceedings of the conference on Design, automation and test in Europe, pp. 624-629. EDA Consortium, 2007.
    """

    def __init__(self, title, **kwargs):
        self.model = {}
        self.__chipModel = {'Cdie': 335 @ u_nF, 'Rdie': 0.1 @ u_mOhm, 'IFlag': 'No'}
        self.__pkgModel = {'Rbump': 0.3 @ u_mOhm, 'Lbump': 0.5e-3 @ u_nH, 'Rppkg': 0.5415 @ u_mOhm, 'Rspkg': 1 @ u_mOhm,
                           'Lspkg': 0.12 @ u_nH, 'Lppkg': 0.00561 @ u_nH, 'Cppkg': 26 @ u_uF}
        self.__pcbModel = {'Rspcb': 0.094 @ u_mOhm, 'Lspcb': 21e-3 @ u_nH, 'Cppcb': 240 @ u_uF,
                           'Rppcb': 0.1666 @ u_mOhm}
        self.model.update(self.__chipModel)
        self.model.update(self.__pkgModel)
        self.model.update(self.__pcbModel)
        self.model.update(**kwargs)
        PowerDeliveryNetworkFactory.__init__(self, title=title)

    def _structure(self):
        vr = PcbRegulatorIdeal(self, amp=1, ac=1, current_flag=1)
        pcb = PcbModelLumped(self, zero_path=False, **self.model)
        # probe = PcbProbeAC(self)
        chip = ChipLumped(self, name='chip', **self.model)  # cannot put name in the dictionary.
        vr.implement(self)
        pcb.implement(self)
        # probe.implement(self)
        chip.implement(self)
        # self.circuit.raw_spice = '.option rshunt = 1.0e12'

    def ac_simulate(self):
        self.simulator = self.circuit.simulator(temperature=25, nominal_temperature=25)
        self.analysis = self.simulator.ac(start_frequency=1e0, stop_frequency=1e9, number_of_points=1000,
                                          variation='dec')

    def plot_impedance(self, label_para=None, label_other=None, reference=None):
        impedance = abs(self.analysis.vdd0 - self.analysis.vss0)
        # impedance = abs(self.analysis['Xchip.diecapVDD'] - self.analysis['Xchip.diecapVSS'])
        freq = self.analysis.frequency
        if label_para is None and label_other is None:
            pass
        elif label_para is not None:
            plt.semilogx(freq, impedance, label=label_para + ': ' + str(self.model.get(label_para)))
        else:
            plt.semilogx(freq, impedance, label=label_other)
        plt.xlim([1e0, 1e9])
        # plt.ylim([0, 9e-3])
        if reference is None:
            return impedance
        else:
            return impedance - reference

    def print_parameter_name(self):
        print(self.model.keys())
        return self.model.keys()
