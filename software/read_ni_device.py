import nidaqmx
from nidaqmx.constants import TerminalConfiguration
import numpy as np
import soundfile as sf

initialized = False
task = None
sample_rate = None
samples_per_channel = None
duration = None

def init_task(sample_rate_param, duration_param, channels):
    global task, sample_rate, samples_per_channel, duration
    sample_rate = sample_rate_param
    duration = duration_param
    samples_per_channel = int(sample_rate * duration)
    task = nidaqmx.Task()
    for i in range(channels):
        task.ai_channels.add_ai_voltage_chan(
            f"cDAQ1Mod1/ai{i}",
            terminal_config=TerminalConfiguration.PSEUDO_DIFF
        )
    task.timing.cfg_samp_clk_timing(
        sample_rate,
        samps_per_chan=samples_per_channel
    )

def acquire_data(verbose=False):
    if verbose:
        print(f"开始采集数据...采样率: {sample_rate}Hz, 时长: {duration}秒")
    data = task.read(
        number_of_samples_per_channel=samples_per_channel,
        timeout=duration + 1
    )
    data = np.array(data).T  # 转置使形状为(采样点数, 通道数)
    dc_offsets = np.mean(data, axis=0)
    if verbose:
        print("各通道原始数据均值(V):")
        for i, offset in enumerate(dc_offsets):
            print(f"通道{i}: {offset:.4f}V")
    data = data - dc_offsets
    return data

def process_and_save_data(processed_data, output_file):
    # 归一化处理(按通道)
    max_vals = np.max(np.abs(processed_data), axis=0)
    for i in range(3):
        if max_vals[i] > 0:
            processed_data[:, i] = processed_data[:, i] / max_vals[i]
    processed_data = np.mean(processed_data, axis=1)

    # 保存为3声道音频文件
    sf.write(output_file, processed_data, sample_rate)
    print(f"平均音频文件已保存: {output_file}")

def finalize():
    task.close()

if __name__ == "__main__":
    sample_rate = 12000  # 采样率(Hz)
    duration = 20  # 采集时长(秒)
    samples_per_channel = sample_rate * duration  # 每通道采样数
    channels = 3  # 使用模块1的通道0-2
    output_file = "output.wav"  # 输出音频文件名

    init_task(sample_rate, duration, channels)
    try:
        data = acquire_data(verbose=True)
        process_and_save_data(data, output_file)
        data2 = acquire_data(verbose=True)
        process_and_save_data(data2, "output2.wav")
    finally:
        finalize()

    print("程序执行完毕")
