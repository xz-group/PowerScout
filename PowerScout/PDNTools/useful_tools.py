import re
import sys


def generate_edge(flag, t, dt, v_l, v_h):
    if re.match('UP', flag, re.I):
        if t - dt < 0:
            return [(t + dt, v_h)]
        else:
            return [(t - dt, v_l), (t + dt, v_h)]
    elif re.match('DOWN', flag, re.I):
        if t - dt < 0:
            return [(t + dt, v_l)]
        else:
            return [(t - dt, v_h), (t + dt, v_l)]
    else:
        sys.exit("EXIT: Wrong flag of Edge! Choose from UP or DOWN.")


def generate_state_movement(t, dt, v0, v1, t_reference=0):
    if t - dt - t_reference < 0:
        return [(t + dt, v1)]
    else:
        return [(t - dt, v0), (t + dt, v1)]


def generate_waveform(initial_value, stop_time, *args, dt=1e-11):
    flag = ["UP", "DOWN"]
    if initial_value == 0 or initial_value == 1:
        waveform = [(0, initial_value)]
    else:
        sys.exit("EXIT: Wrong initial_value! Choose from 1 or 0.")
    for time in args:
        waveform.extend(generate_edge(flag[waveform[-1][-1]], time, dt, 0, 1))

    if stop_time <= waveform[-1][0]:
        return waveform[0:-1]
    else:
        waveform.append((stop_time, waveform[-1][-1]))
        return waveform


def generate_waveform_from_seq(seq, frequency, dt=1e-10, amp=1):
    flag = ["UP", "DOWN"]
    time = 0
    period = 1 / frequency
    waveform = [(0, 0)]
    for state in seq:
        if state == waveform[-1][-1]:
            time += period
        else:
            waveform.extend(generate_edge(flag[waveform[-1][-1]], time, dt, 0, 1))
            time += period
    waveform.append((time + 0.5 * period, waveform[-1][-1]))
    for i in range(len(waveform)):
        waveform[i] = (waveform[i][0], waveform[i][1] * amp)
    return waveform


def generate_waveform_from_amplitudes(amplitudes, frequency, delay=0, stop_time=None, dt=1e-10):
    time = 0
    period = 1 / frequency
    waveform = [(0, 0)]
    if delay != 0:
        waveform.append((delay, waveform[-1][-1]))
        time += delay
    for state in amplitudes:
        if state == waveform[-1][-1]:
            time += period
        else:
            waveform.extend(generate_state_movement(time, dt, waveform[-1][-1], state, t_reference=delay))
            time += period
        if stop_time is not None:
            if time > stop_time:
                waveform.append((stop_time, waveform[-1][-1]))
                break
    return waveform


def generate_waveform_from_amplitudes_for_PSD(amplitudes, frequency, dt=1e-10):
    time = 0
    time_ = 0
    period = 1 / frequency
    time_list = [0]
    voltage_list = [0]
    for state in amplitudes:
        time += period
        while True:
            if time_ <= time:
                time_ += dt
                time_list.append(time_)
                voltage_list.append(voltage_list[-1])
            else:
                time_list.append(time_)
                voltage_list.append(state)
                time += dt
                break

    return time_list, voltage_list
