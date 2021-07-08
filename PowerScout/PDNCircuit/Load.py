from PowerScout.PDNCircuit.Basic import *
from PowerScout.PDNTools.useful_tools import generate_waveform


class CurrentLoadSquareWave(SubCircuit, Block4Ports):
    DEFAULT_NAME = 'CurrentLoadSquareWave'

    def __init__(self, pdn, name=None, if_time_waveform=False, *, tstop, waveform):
        self.tstop = tstop
        self.waveform = waveform
        self.if_time_waveform = if_time_waveform
        if name is not None:
            self.sub_name = name
        else:
            self.sub_name = self.DEFAULT_NAME
        SubCircuit.__init__(self, self.sub_name, *self.NODES)
        self._model()
        pdn.circuit.subcircuit(self)

    def _model(self):
        if self.if_time_waveform is False:
            self.PieceWiseLinearCurrentSource('load1', 'VDD1', 'VSS1',
                                              generate_waveform(0, self.tstop, *self.waveform))
            self.PieceWiseLinearVoltageSource('ctrl1', 'VDD2', 'VSS2',
                                              generate_waveform(0, self.tstop, *self.waveform))
        else:
            self.PieceWiseLinearCurrentSource('load1', 'VDD1', 'VSS1', self.waveform)
            self.PieceWiseLinearVoltageSource('ctrl1', 'VDD2', 'VSS2', self.waveform)

    def implement_measure(self, pdn, br_flag=""):
        pdn.circuit.X(self.sub_name + str(pdn.nodes_count) + br_flag, self.sub_name,
                      self.GLOBAL_VDD + str(pdn.nodes_count) + br_flag,
                      self.GLOBAL_VSS + str(pdn.nodes_count) + br_flag,
                      self.GLOBAL_VDD + 'M',
                      self.GLOBAL_VSS + 'M')
        # self._add_nodes_count(pdn)
        self._append_nodes_pair(pdn, br_flag)
