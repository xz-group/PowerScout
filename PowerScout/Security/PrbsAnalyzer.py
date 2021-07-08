import numpy as np
import statistics
import pandas as pd
from scipy.interpolate import interp1d
from PowerScout.PDNTools.lfsr import LinearFeedbackShiftRegister
from PowerScout.PDNTools.useful_tools import generate_waveform_from_seq
import math
import matplotlib.pyplot as plt
from scipy.fftpack import fft
from scipy.signal.windows.windows import blackman


class PrbsAnalyzer:
    """
    Gain the frequency response with PRBS input signals

    analyzer_golden = PrbsAnalyzer(PdnBoardV1p3_Gold)
    analyzer_golden.prbs_run_analysis()
    analyzer_golden.plot_pdn_ac()
    analyzer_golden.plot_pdn_spectrum(mode='.')
    analyzer_golden.plot_pdn_spectrum_raw(mode='--')
    plt.yscale('log')
    plt.show()
    """

    def __init__(self, pdn_class_name, prbs_bit_rate=1e8, prbs_size=7, prbs_num_repetition=1, sampling_frequency=1e9,
                 prbs_current=0.01, dt=1e-9, start_freq=50e3, stop_freq=1e9, padding_coefficient=1):

        self.prbs_bit_rate = prbs_bit_rate
        self.sampling_freq = sampling_frequency
        self.prbs_size = prbs_size
        self.prbs_num_repetition = prbs_num_repetition
        self.dt = dt
        self.prbs_current_amp = prbs_current
        self.start_freq = start_freq
        self.stop_freq = stop_freq
        self.padding_coefficient = padding_coefficient

        # None variables
        self.tstop = None
        self.pdn_time = None
        self.pdn_prbs = None
        self.pdn_response = None
        self.pdn_freq = None
        self.pdn_impedance = None
        self.pdn_response_auto_corr = None
        self.pdn_prbs_auto_corr = None
        self.pdn_prbs_response_cross_corr = None
        self.pdn_response_spectrum_raw = None
        self.pdn_response_spectrum = None
        self.pdn_prbs_spectrum_raw = None
        self.pdn_prbs_spectrum = None
        self.pdn_spectrum_raw = None
        self.pdn_spectrum = None
        self.freq_raw = None
        self.freq = None
        self.prbs = None
        self.waveform = None

        self._generate_prbs_waveform()
        # self.pdn_ac = pdn_class_name(title='dut_ac', if_print_circuit=False)
        self.pdn_trans = pdn_class_name(title='dut_trans', seq_waveform=self.waveform, if_print_circuit=False)

    def ac_simulate(self, if_write_cvs=False, csv_title=None):
        self.pdn_trans.ac_simulate(start_freq=self.start_freq, stop_freq=self.stop_freq)
        result = self.pdn_trans.plot_impedance(if_plot=False)
        self.pdn_freq = result[0]
        self.pdn_impedance = result[1]
        # print(result)
        if if_write_cvs:
            dataframe = pd.DataFrame({'freq': self.pdn_freq, 'impedance': self.pdn_impedance})
            dataframe.to_csv(csv_title + '.csv', index=False, sep=',')

    def trans_simulate(self, if_write_cvs=False, csv_title=None):
        self.tstop = self.waveform[-1][0]
        self.pdn_trans.transient_simulate(tstop=self.tstop)
        result = self.pdn_trans.plot_waveform(if_print=True, if_plot=False)
        time = result.get('time')
        voltage = result.get('voltage')  # PDN response
        waveform = result.get('waveform')  # input PRBS signal
        # define interp1d functions
        f_voltage = interp1d(time, voltage, kind='linear')
        f_waveform = interp1d(time, waveform, kind='linear')

        tstop = float(time[-1])
        self.pdn_time = np.linspace(0, tstop, math.floor(tstop * self.sampling_freq))
        self.pdn_response = f_voltage(self.pdn_time)
        self.pdn_prbs = f_waveform(self.pdn_time)

        if if_write_cvs:
            dataframe = pd.DataFrame(
                {'time': self.pdn_time, 'pdn_response': self.pdn_response, 'prbs_signal': self.pdn_prbs})
            dataframe.to_csv(csv_title + '.csv', index=False, sep=',')

    def prbs_run_analysis(self):
        self.trans_simulate()
        self.ac_simulate()
        self.pdn_prbs_auto_corr = self._auto_correlation(self.pdn_prbs)
        self.pdn_response_auto_corr = self._auto_correlation(self.pdn_response)
        [self.pdn_prbs_spectrum_raw, self.pdn_prbs_spectrum] = self._corr_spectrum(self.pdn_prbs_auto_corr)
        [self.pdn_response_spectrum_raw, self.pdn_response_spectrum] = self._corr_spectrum(self.pdn_response_auto_corr)
        self.pdn_prbs_response_cross_corr = self._cross_correlation(self.pdn_response, self.pdn_prbs)
        # [self.pdn_spectrum_raw, self.pdn_spectrum] = self._corr_spectrum(self.pdn_response_auto_corr,
        #                                                                  self.pdn_prbs_spectrum_raw,
        #                                                                  if_sqrt=True)
        [self.pdn_spectrum_raw, self.pdn_spectrum] = self._corr_spectrum(self.pdn_prbs_response_cross_corr,
                                                                         self.pdn_prbs_spectrum_raw)

    def _generate_prbs_waveform(self):
        self.prbs = LinearFeedbackShiftRegister(m=self.prbs_size)
        self.prbs.runFullCycle(k=self.prbs_num_repetition)
        self.waveform = generate_waveform_from_seq(self.prbs.seq, self.prbs_bit_rate, dt=self.dt,
                                                   amp=self.prbs_current_amp)

    def _corr_spectrum(self, input_corr, input_spectrum=None, if_sqrt=False):
        input_n = len(input_corr)
        w = blackman(input_n)  # add window
        # padding zeros to increase the FFT resolution.
        # Note this does not actually increase the information.
        input_n = input_n * self.padding_coefficient
        # fourier = fft(input_corr, input_n)
        fourier = fft(input_corr * w, input_n)
        fourier = 2.0 / input_n * np.abs(fourier[0:input_n // 2])
        xf = np.linspace(0, self.sampling_freq / 2, input_n // 2)
        if input_spectrum is not None:
            fourier = fourier / input_spectrum

        step = self.prbs_bit_rate / self.prbs.expectedPeriod
        freq_list = [step]
        while freq_list[-1] <= self.sampling_freq / 2:
            freq_list.append(freq_list[-1] + step)

        amp_list = []
        for i in range(len(freq_list)):
            # find the nearest value in the list
            xf_ = list(abs(xf - freq_list[i]))
            index = xf_.index(min(xf_))
            amp_list.append(fourier[index])
            freq_list[i] = xf[index]

        if if_sqrt:
            fourier = np.sqrt(fourier)
            amp_list = np.sqrt(amp_list)

        self.freq_raw = xf
        spectrum_raw = fourier
        self.freq = freq_list
        spectrum = amp_list
        # print(self.prbs.expectedPeriod)
        return spectrum_raw, spectrum

    @staticmethod
    def _cross_correlation(input1, input2, mode='full'):
        return np.correlate(input1 - statistics.mean(input1), input2 - statistics.mean(input2), mode)

    @staticmethod
    def _auto_correlation(input1, mode='full'):
        input1 = input1 * 1.0
        return np.correlate(input1 - statistics.mean(input1), input1 - statistics.mean(input1), mode)

    def plot_pdn_ac(self, start_freq=None, stop_freq=None, mode='-', color=None, label=None):
        if stop_freq is None:
            stop_freq = self.stop_freq
        if start_freq is None:
            start_freq = self.start_freq
        plt.semilogx(self.pdn_freq, self.pdn_impedance, mode, color=color, label=label)
        plt.xlim([start_freq, stop_freq])

    def plot_pnd_response_trans(self, tstart=None, tstop=None, mode='-', color=None, label=None):
        if tstart is None:
            tstart = 0
        if tstop is None:
            tstop = self.tstop / self.prbs_num_repetition
        plt.plot(self.pdn_time, self.pdn_response, mode, color=color, label=label)
        plt.xlim([tstart, tstop])

    def plot_pnd_prbs_trans(self, tstart=None, tstop=None, mode='-', color=None, label=None):
        if tstart is None:
            tstart = 0
        if tstop is None:
            tstop = self.tstop / self.prbs_num_repetition
        plt.plot(self.pdn_time, self.pdn_prbs, mode, color=color, label=label)
        plt.xlim([tstart, tstop])

    def plot_prbs_auto_corr(self, mode='-', tstart=None, tstop=None, color=None, label=None):
        self._plot_correlation(self.pdn_prbs_auto_corr, mode, color=color, label=label)
        # if tstart is None:
        #     tstart = -self.tstop
        # if tstop is None:
        #     tstop = self.tstop
        # plt.xlim([tstart, tstop])

    def plot_pdn_auto_corr(self, mode='-', tstart=None, tstop=None, color=None, label=None):
        self._plot_correlation(self.pdn_response_auto_corr, mode, color=color, label=label)
        # if tstart is None:
        #     tstart = -self.tstop
        # if tstop is None:
        #     tstop = self.tstop
        # plt.xlim([tstart, tstop])

    def plot_pdn_prbs_response_cross_corr(self, tstart=None, tstop=None, mode='-', color=None, label=None):
        self._plot_correlation(self.pdn_prbs_response_cross_corr, mode, color=color, label=label)
        # if tstart is None:
        #     tstart = -self.tstop
        # if tstop is None:
        #     tstop = self.tstop
        # plt.xlim([tstart, tstop])

    def plot_prbs_spectrum(self, start_freq=None, stop_freq=None, mode='-', color=None, label=None):
        plt.semilogx(self.freq, self.pdn_prbs_spectrum, mode, color=color, label=label)
        if stop_freq is None:
            stop_freq = self.stop_freq
        if start_freq is None:
            start_freq = self.start_freq
        plt.xlim([start_freq, stop_freq])

    def plot_pdn_response_spectrum(self, start_freq=None, stop_freq=None, mode='-', color=None, label=None):
        plt.semilogx(self.freq, self.pdn_response_spectrum, mode, color=color, label=label)
        if stop_freq is None:
            stop_freq = self.stop_freq
        if start_freq is None:
            start_freq = self.start_freq
        plt.xlim([start_freq, stop_freq])

    def plot_pdn_response_spectrum_raw(self, start_freq=None, stop_freq=None, mode='-', color=None, label=None):
        plt.semilogx(self.freq_raw, self.pdn_response_spectrum_raw, mode, color=color, label=label)
        if stop_freq is None:
            stop_freq = self.stop_freq
        if start_freq is None:
            start_freq = self.start_freq
        plt.xlim([start_freq, stop_freq])

    def plot_prbs_spectrum_raw(self, start_freq=None, stop_freq=None, mode='-', color=None, label=None):
        plt.semilogx(self.freq_raw, self.pdn_prbs_spectrum_raw, mode, color=color, label=label)
        if stop_freq is None:
            stop_freq = self.stop_freq
        if start_freq is None:
            start_freq = self.start_freq
        plt.xlim([start_freq, stop_freq])

    def plot_pdn_spectrum(self, start_freq=None, stop_freq=None, mode='-', color=None, label=None):
        plt.semilogx(self.freq, self.pdn_spectrum, mode, color=color, label=label)
        if stop_freq is None:
            stop_freq = self.stop_freq
        if start_freq is None:
            start_freq = self.start_freq
        plt.xlim([start_freq, stop_freq])

    def plot_pdn_spectrum_raw(self, start_freq=None, stop_freq=None, mode='-', color=None, label=None):
        plt.semilogx(self.freq_raw, self.pdn_spectrum_raw, mode, color=color, label=label)
        if stop_freq is None:
            stop_freq = self.stop_freq
        if start_freq is None:
            start_freq = self.start_freq
        plt.xlim([start_freq, stop_freq])

    @staticmethod
    def _plot_correlation(input_corr, mode='-', color=None, label=None):
        plt.plot(
            np.linspace(-(len(input_corr) - 1) / 2, (len(input_corr) - 1) / 2, len(input_corr)) / (len(input_corr)),
            input_corr, mode, color=color, label=label)
