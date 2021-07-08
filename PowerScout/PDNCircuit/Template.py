import matplotlib.pyplot as plt
from PowerScout.PDNCircuit.Regulator import *
from PowerScout.PDNCircuit.Chip import *
from PowerScout.PDNCircuit.Load import *


# todo: change the structure to Pdn2007DateLumped
class TemplatePdnDATE07(PowerDeliveryNetworkFactory):
    """ Built-in PDN template based on the 2007 DATE paper.
        This class contains both lumped and distributed models.
        Reference:
        Gupta, Meeta S., Jarod L. Oatley, Russ Joseph, Gu-Yeon Wei, and David M. Brooks.
        "Understanding voltage variations in chip multiprocessors using a distributed power-delivery network."
        In Proceedings of the conference on Design, automation and test in Europe, pp. 624-629. EDA Consortium, 2007.
    """

    def __init__(self, title, is_distributed, **kwargs):
        self._model = {}
        self._is_distributed = is_distributed
        if self._is_distributed:
            self._init_para_distributed(**kwargs)
        else:
            self._init_para_lumped(**kwargs)
        PowerDeliveryNetworkFactory.__init__(self, title=title)

    def _init_para_distributed(self, **kwargs):
        # Todo: Try to separate the current load from the chip 暴露接口，load统一由其他的类来完成
        chip_model = {'Xstop': 12, 'Ystop': 12, 'C4numX': 10, 'C4numY': 10, 'C4shift': 0,
                      'Cdie': 2.2 @ u_nF,
                      'Rdie': 50 @ u_mOhm, 'Ldie': 5.6e-6 @ u_nH, 'IFlag': 'All', 'Iload': [(5, 5)]}

        pkg_model = {'Rbump': 40 @ u_mOhm, 'Lbump': 72e-3 @ u_nH, 'Rppkg': 0.5415 @ u_mOhm, 'Rspkg': 1 @ u_mOhm,
                     'Lspkg': 120e-3 @ u_nH, 'Lppkg': 5.61e-3 @ u_nH, 'Cppkg': 26 @ u_uF}
        pcb_model = {'Rs': 0.094 @ u_mOhm, 'Ls': 21e-3 @ u_nH, 'Cp': 240 @ u_uF, 'Rp': 0.1666 @ u_mOhm}
        self._model.update(chip_model)
        self._model.update(pkg_model)
        self._model.update(pcb_model)
        self._model.update(**kwargs)  # for changing some parameters of the PDN _model

    def _init_para_lumped(self, **kwargs):
        chip_model = {'Cdie': 335 @ u_nF, 'Rdie': 0.1 @ u_mOhm, 'IFlag': 'Yes'}
        pkg_model = {'Rbump': 0.3 @ u_mOhm, 'Lbump': 0.5e-3 @ u_nH, 'Rppkg': 0.5415 @ u_mOhm, 'Rspkg': 1 @ u_mOhm,
                     'Lspkg': 0.12 @ u_nH, 'Lppkg': 0.00561 @ u_nH, 'Cppkg': 26 @ u_uF}
        pcb_model = {'Rspcb': 0.094 @ u_mOhm, 'Lspcb': 21e-3 @ u_nH, 'Cppcb': 240 @ u_uF,
                     'Rppcb': 0.1666 @ u_mOhm}
        self._model.update(chip_model)
        self._model.update(pkg_model)
        self._model.update(pcb_model)
        self._model.update(**kwargs)  # for changing some parameters of the PDN _model

    def _structure(self):
        vr = PcbRegulatorIdeal(self, amp=1)
        pcb = PcbModelLumped(self, **self._model)
        if self._is_distributed:
            chip = ChipSingleCore(self, name='chip', **self._model)
        else:  # lumped model
            chip = ChipLumped(self, name='chip', **self._model)  # cannot put name in the dictionary.
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
        pcb = PcbModelLumped(self, is_zero_ground=False, **self.model)
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
        pcb = PcbModelLumped(self, is_zero_ground=False, **self.model)
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
        pcb = PcbModelLumped(self, is_zero_ground=False, **self.model)
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


class TemplatePdnTCPMT14(PowerDeliveryNetworkFactory):
    """
    built in pdn based on the 2014 TCPMT paper (three anti-resonant frequency points)

    Reference:
    Zhang X, Liu Y, Hu X, Cheng CK. Ratio of the Worst Case Noise and the Impedance of Power Distribution Network. IEEE
    Transactions on Components, Packaging and Manufacturing Technology. 2014 Jun 30;4(8):1325-34.
    """

    def __init__(self, title, waveform=None, seq_waveform=None, if_print_circuit=True, **kwargs):
        self.waveform = waveform
        self.seq_waveform = seq_waveform
        PowerDeliveryNetworkFactory.__init__(self, title=title)
        if if_print_circuit:
            print(self.circuit)

    def _structure(self):
        vr = PcbRegulatorIdeal(self, amp=1)
        rlc1 = BasicCircuitRLC(self, name='vrm', res_s=5 @ u_mOhm, ind_s=16.7 @ u_nH, cap_p=30 @ u_uF,
                               res_p=0.5 @ u_mOhm,
                               ind_p=0.3 @ u_nH, is_zero_ground=True)
        rlc2 = BasicCircuitRLC(self, name='pcb', res_s=5 @ u_mOhm, ind_s=1 @ u_nH, cap_p=1 @ u_uF,
                               res_p=0.8 @ u_mOhm,
                               ind_p=3e-3 @ u_nH, is_zero_ground=True)
        rlc3 = BasicCircuitRLC(self, name='chip', res_s=10 @ u_mOhm, ind_s=100e-3 @ u_nH, cap_p=30 @ u_nF,
                               res_p=5 @ u_mOhm,
                               ind_p=0 @ u_nH, is_zero_ground=True)
        if self.waveform is not None:
            tran_load = CurrentLoadSquareWave(self, tstop=0, waveform=self.waveform)
        elif self.seq_waveform is not None:
            tran_load = CurrentLoadSquareWave(self, tstop=0, waveform=self.seq_waveform, if_time_waveform=True)
        probe = PcbProbeAC(self)
        vr.implement(self)
        rlc1.implement(self)
        rlc2.implement(self)
        rlc3.implement(self)
        probe.implement(self)
        if self.waveform is not None or self.seq_waveform is not None:
            tran_load.implement(self)
        self.circuit.raw_spice = '.option rshunt = 1.0e12'

    def ac_simulate(self, start_freq=1e4, stop_freq=1e9, num_points=1000):
        self.simulator = self.circuit.simulator(temperature=25, nominal_temperature=25)
        self.analysis = self.simulator.ac(start_frequency=start_freq, stop_frequency=stop_freq,
                                          number_of_points=num_points,
                                          variation='dec')

    def plot_impedance(self, label_para=None, label_other=None, frequency=None):
        impedance = abs(self.analysis.vdd3 - self.analysis.vss3)
        freq = self.analysis.frequency
        if label_para is None and label_other is None:
            plt.semilogx(freq, impedance)
        # plt.xlim([1e4, 1e9])
        # plt.ylim([0, 9e-3])
        if frequency is None:
            return impedance
        else:
            return [freq, impedance]

    def transient_simulate(self, tstop=None):
        self.tstop = tstop
        self.simulator = self.circuit.simulator(temperature=25, nominal_temperature=25)
        self.analysis = self.simulator.transient(step_time=10 @ u_ns, end_time=tstop, start_time=0,
                                                 max_time=100 @ u_ns)

    def plot_waveform(self, if_print=False, if_plot=True):
        voltage = self.analysis.vdd3 - self.analysis.vss3
        waveform = self.analysis.vdd4 - self.analysis.vss4
        time = self.analysis.time
        if if_plot:
            plt.subplot(2, 1, 1)
            plt.plot(time, voltage)
            plt.xlim([0, self.tstop])
            # plt.xlabel('time')
            plt.grid()
            plt.subplot(2, 1, 2)
            plt.plot(time, waveform)
            plt.grid()
            plt.xlim([0, self.tstop])
            plt.xlabel('time')
        if if_print:
            return {'time': time, 'voltage': voltage, 'waveform': waveform}

    def print_parameter_name(self):
        print(self.model.keys())
        return self.model.keys()


class PdnBoardV1p3(PowerDeliveryNetworkFactory):
    def __init__(self, title, waveform=None, seq_waveform=None, if_print_circuit=True, **kwargs):
        self.waveform = waveform
        self.seq_waveform = seq_waveform
        PowerDeliveryNetworkFactory.__init__(self, title=title)
        if if_print_circuit:
            print(self.circuit)

    def ac_simulate(self, start_freq=1e3, stop_freq=1e9, num_points=1000, temp=25, nominal_temp=25, variation='dec'):
        self.simulator = self.circuit.simulator(temperature=temp, nominal_temperature=nominal_temp)
        self.analysis = self.simulator.ac(start_frequency=start_freq, stop_frequency=stop_freq,
                                          number_of_points=num_points,
                                          variation=variation)

    def plot_impedance(self):
        impedance = abs(self.analysis.vdd0 - self.analysis.vss0)
        # impedance = abs(self.analysis['XChipLumped.diecapVDD'] - self.analysis['XChipLumped.diecapVSS'])
        freq = self.analysis.frequency
        plt.semilogx(freq, impedance)
        # plt.ylim([1e-4, 100])
        plt.xlim([1e5, 1e9])

    def transient_simulate(self, tstop=None):
        self.tstop = tstop
        self.simulator = self.circuit.simulator(temperature=25, nominal_temperature=25)
        self.analysis = self.simulator.transient(step_time=10 @ u_ns, end_time=tstop, start_time=0,
                                                 max_time=100 @ u_ns)

    def plot_waveform(self, if_print=False, if_plot=True):
        voltage = self.analysis.vdd1 - self.analysis.vss1
        waveform = self.analysis.vddM - self.analysis.vssM
        time = self.analysis.time
        if if_plot:
            plt.subplot(2, 1, 1)
            plt.plot(time, voltage)
            plt.xlim([0, self.tstop])
            # plt.xlabel('time')
            plt.grid()
            plt.subplot(2, 1, 2)
            plt.plot(time, waveform)
            plt.grid()
            plt.xlim([0, self.tstop])
            plt.xlabel('time')
        if if_print:
            return {'time': time, 'voltage': voltage, 'waveform': waveform}


class PdnBoardV1p3_Gold(PdnBoardV1p3):

    def _structure(self):
        vr = PcbBuckConverter(self, name='VRM', voltage=1.2, res_s=200 @ u_mOhm, ind_s=15 @ u_nH, cap_p=10 @ u_uF,
                              res_p=30 @ u_mOhm, ind_p=10 @ u_nH)
        cap4p7uf = PcbCapacitorSimple(self, name='cap4p7uf', R=15 @ u_mOhm, L=1 @ u_nH, C=4 @ u_uF, LM=2.6171 @ u_nH)
        cap0p1uf = PcbCapacitorSimple(self, name='cap0p1uf', R=10 @ u_mOhm, L=0.6 @ u_nH, C=0.1 @ u_uF,
                                      LM=2.6171 @ u_nH)
        ac_probe = PcbProbeAC(self, current_flag=1)
        wireline = PcbWireLine(self, Rs=50 @ u_mOhm, Ls=10 @ u_nH)
        res = PcbSamplingResistor(self, Rs=1)
        chipM = BasicCircuitRLC(self, name='chipM', res_s=0 @ u_mOhm, ind_s=0 @ u_nH, cap_p=0.9 @ u_nF,
                                res_p=3000 @ u_mOhm, ind_p=21 @ u_nH, is_zero_ground=True)
        chip = BasicCircuitRLC(self, name='chip', res_s=0 @ u_mOhm, ind_s=0 @ u_nH, cap_p=0.59 @ u_nF,
                               res_p=580 @ u_mOhm, ind_p=11.6 @ u_nH, is_zero_ground=True)
        if self.waveform is not None:
            tran_load = CurrentLoadSquareWave(self, tstop=0, waveform=self.waveform)
        elif self.seq_waveform is not None:
            tran_load = CurrentLoadSquareWave(self, tstop=0, waveform=self.seq_waveform, if_time_waveform=True)

        vr.implement(self)
        for i in range(2):
            cap4p7uf.implement(self, name=cap4p7uf.sub_name + str(i))
        for i in range(5):
            cap0p1uf.implement(self, name=cap4p7uf.sub_name + str(i))

        wireline.implement(self)
        # res.implement(self)
        ac_probe.implement(self)
        if self.waveform is not None or self.seq_waveform is not None:
            tran_load.implement_measure(self)
        # chipM.implement(self)
        chip.implement(self)
        self.circuit.raw_spice = '.option rshunt = 1.0e12'

    def plot_impedance(self, if_plot=True):
        impedance = abs(self.analysis.vdd1 - self.analysis.vss1)
        freq = self.analysis.frequency
        if if_plot:
            plt.semilogx(freq, impedance)
        # plt.xlim([1e5, 1e9])
        return freq, impedance


class PdnBoardV1p3_Resistor(PdnBoardV1p3):

    def _structure(self):
        vr = PcbBuckConverter(self, name='VRM', voltage=1.2, res_s=200 @ u_mOhm, ind_s=15 @ u_nH, cap_p=10 @ u_uF,
                              res_p=30 @ u_mOhm, ind_p=10 @ u_nH)
        cap4p7uf = PcbCapacitorSimple(self, name='cap4p7uf', R=15 @ u_mOhm, L=1 @ u_nH, C=4 @ u_uF, LM=2.6171 @ u_nH)
        cap0p1uf = PcbCapacitorSimple(self, name='cap0p1uf', R=10 @ u_mOhm, L=0.6 @ u_nH, C=0.1 @ u_uF,
                                      LM=2.6171 @ u_nH)
        ac_probe = PcbProbeAC(self, current_flag=1)
        wireline = PcbWireLine(self, Rs=50 @ u_mOhm, Ls=10 @ u_nH)
        res = PcbSamplingResistor(self, Rs=1)
        chipM = BasicCircuitRLC(self, name='chipM', res_s=0 @ u_mOhm, ind_s=0 @ u_nH, cap_p=0.9 @ u_nF,
                                res_p=3000 @ u_mOhm, ind_p=21 @ u_nH, is_zero_ground=True)
        chip = BasicCircuitRLC(self, name='chip', res_s=0 @ u_mOhm, ind_s=0 @ u_nH, cap_p=0.59 @ u_nF,
                               res_p=580 @ u_mOhm, ind_p=11.6 @ u_nH, is_zero_ground=True)
        if self.waveform is not None:
            tran_load = CurrentLoadSquareWave(self, tstop=0, waveform=self.waveform)
        elif self.seq_waveform is not None:
            tran_load = CurrentLoadSquareWave(self, tstop=0, waveform=self.seq_waveform, if_time_waveform=True)

        vr.implement(self)
        for i in range(2):
            cap4p7uf.implement(self, name=cap4p7uf.sub_name + str(i))
        for i in range(5):
            cap0p1uf.implement(self, name=cap4p7uf.sub_name + str(i))

        wireline.implement(self)
        res.implement(self)
        ac_probe.implement(self)
        if self.waveform is not None or self.seq_waveform is not None:
            tran_load.implement_measure(self)
        # chipM.implement(self)
        chip.implement(self)
        self.circuit.raw_spice = '.option rshunt = 1.0e12'

    def plot_impedance(self, if_plot=True):
        impedance = abs(self.analysis.vdd2 - self.analysis.vss2)
        freq = self.analysis.frequency
        if if_plot:
            plt.semilogx(freq, impedance)
        # plt.xlim([1e5, 1e9])
        return freq, impedance

    def plot_waveform(self, if_print=False, if_plot=True):
        voltage = self.analysis.vdd2 - self.analysis.vss2
        waveform = self.analysis.vddM - self.analysis.vssM
        time = self.analysis.time
        if if_plot:
            plt.subplot(2, 1, 1)
            plt.plot(time, voltage)
            plt.xlim([0, self.tstop])
            # plt.xlabel('time')
            plt.grid()
            plt.subplot(2, 1, 2)
            plt.plot(time, waveform)
            plt.grid()
            plt.xlim([0, self.tstop])
            plt.xlabel('time')
        if if_print:
            return {'time': time, 'voltage': voltage, 'waveform': waveform}

class PdnBoardV1p3_Malicious(PdnBoardV1p3):

    def _structure(self):
        vr = PcbBuckConverter(self, name='VRM', voltage=1.2, res_s=200 @ u_mOhm, ind_s=15 @ u_nH, cap_p=10 @ u_uF,
                              res_p=30 @ u_mOhm, ind_p=10 @ u_nH)
        cap4p7uf = PcbCapacitorSimple(self, name='cap4p7uf', R=15 @ u_mOhm, L=1 @ u_nH, C=4 @ u_uF, LM=2.6171 @ u_nH)
        cap0p1uf = PcbCapacitorSimple(self, name='cap0p1uf', R=10 @ u_mOhm, L=0.6 @ u_nH, C=0.1 @ u_uF,
                                      LM=2.6171 @ u_nH)
        ac_probe = PcbProbeAC(self, current_flag=1)
        wireline = PcbWireLine(self, Rs=50 @ u_mOhm, Ls=10 @ u_nH)
        res = PcbSamplingResistor(self, Rs=1)
        chipM = BasicCircuitRLC(self, name='chipM', res_s=0 @ u_mOhm, ind_s=0 @ u_nH, cap_p=0.9 @ u_nF,
                                res_p=3000 @ u_mOhm, ind_p=21 @ u_nH, is_zero_ground=True)
        chip = BasicCircuitRLC(self, name='chip', res_s=0 @ u_mOhm, ind_s=0 @ u_nH, cap_p=0.59 @ u_nF,
                               res_p=580 @ u_mOhm, ind_p=11.6 @ u_nH, is_zero_ground=True)
        if self.waveform is not None:
            tran_load = CurrentLoadSquareWave(self, tstop=0, waveform=self.waveform)
        elif self.seq_waveform is not None:
            tran_load = CurrentLoadSquareWave(self, tstop=0, waveform=self.seq_waveform, if_time_waveform=True)

        vr.implement(self)
        for i in range(2):
            cap4p7uf.implement(self, name=cap4p7uf.sub_name + str(i))
        for i in range(5):
            cap0p1uf.implement(self, name=cap4p7uf.sub_name + str(i))

        wireline.implement(self)
        # res.implement(self)
        ac_probe.implement(self)
        if self.waveform is not None or self.seq_waveform is not None:
            tran_load.implement_measure(self)
        chipM.implement(self)
        chip.implement(self)
        self.circuit.raw_spice = '.option rshunt = 1.0e12'

    def plot_impedance(self, if_plot=True):
        impedance = abs(self.analysis.vdd1 - self.analysis.vss1)
        freq = self.analysis.frequency
        if if_plot:
            plt.semilogx(freq, impedance)
        # plt.xlim([1e5, 1e9])
        return freq, impedance

    def plot_waveform(self, if_print=False, if_plot=True):
        voltage = self.analysis.vdd1 - self.analysis.vss1
        waveform = self.analysis.vddM - self.analysis.vssM
        time = self.analysis.time
        if if_plot:
            plt.subplot(2, 1, 1)
            plt.plot(time, voltage)
            plt.xlim([0, self.tstop])
            # plt.xlabel('time')
            plt.grid()
            plt.subplot(2, 1, 2)
            plt.plot(time, waveform)
            plt.grid()
            plt.xlim([0, self.tstop])
            plt.xlabel('time')
        if if_print:
            return {'time': time, 'voltage': voltage, 'waveform': waveform}
