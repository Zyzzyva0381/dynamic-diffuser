import numpy as np
import wave
import struct

# Parameters
frequency = 3400  # Hz
duration = 20  # seconds
sample_rate = 44100  # Hz
volume = 32767  # Max amplitude for 16-bit audio

# Generate time points
t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

# Generate sine wave
data = np.sin(2 * np.pi * frequency * t)

# Scale to 16-bit integer values
scaled_data = (data * volume).astype(np.int16)

# Open a new wave file
file_name = f"sine_{frequency}Hz_{duration}s.wav"
with wave.open(file_name, 'w') as wav_file:
    # Set the parameters
    n_channels = 1  # Mono
    sampwidth = 2  # 2 bytes for 16-bit audio
    n_frames = len(scaled_data)
    comptype = "NONE"
    compname = "not compressed"

    wav_file.setparams((n_channels, sampwidth, sample_rate, n_frames, comptype, compname))

    # Write the frames
    for s in scaled_data:
        wav_file.writeframes(struct.pack('h', s))

print(f"Generated {file_name}")
