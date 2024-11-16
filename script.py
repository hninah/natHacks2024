import serial
import time
import numpy as np
import matplotlib.pyplot as plt
from brainflow.board_shim import BoardShim, BrainFlowInputParams
from scipy.signal import butter, lfilter

# Configuration
COM_PORT = "COM13"  
BAUD_RATE = 115200  
EEG_THRESHOLD = 500  
EEG_SCALING_FACTOR = 0.02  

# # Connect to Arduino
arduino = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
time.sleep(2)  # Allow time for Arduino connection to establish
print("Connected to Arduino\n")

def send_command(command):
    """Send a command to the Arduino via serial."""
    arduino.write((command + "\r\n").encode())  # Add \r\n for "Both NL & CR"
    print(f"Sent to Arduino: {command}")
    time.sleep(0.1)  # Small delay to ensure Arduino processes the command

def process_eeg_data(eeg_data):
    """Process EEG data to extract meaningful features."""
    # Example: Use mean and max of absolute EEG values
    eeg_values = np.array(eeg_data)
    abs_mean = np.mean(np.abs(eeg_values))
    max_peak = np.max(np.abs(eeg_values))
    return abs_mean, max_peak

def calculate_stimulation_params(abs_mean, max_peak):
    """Determine AMPL, DURN, and FREQ based on processed EEG data."""
    ampl = int(min(max(10, abs_mean * EEG_SCALING_FACTOR), 30))  # Scale to 5-20 mA
    durn = int(min(max(150, max_peak * EEG_SCALING_FACTOR), 200))  # Scale to 100-200 µs
    freq = 20 if abs_mean > EEG_THRESHOLD else 10  # Adjust frequency based on mean
    return ampl, durn, freq


# Muse 2 EEG Streaming Configuration
params = BrainFlowInputParams()
params.serial_port = 'COM14' 
board_id = 38  
fs = 256  

# Bandpass Filter Function
def bandpass_filter(data, lowcut, highcut, fs, order=4):
    """Apply a Butterworth bandpass filter."""
    nyquist = 0.5 * fs  
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype='band')
    y = lfilter(b, a, data)
    return y

try:
    # Initialize Muse 2 connection
    board = BoardShim(board_id, params)
    board.prepare_session()
    print("Successfully prepared Muse 2 session.")
    board.start_stream()

    # Set up live plot for EEG bands
    plt.ion()
    fig, axs = plt.subplots(5, 1, figsize=(10, 8))
    wave_names = ['Delta (0.5–4 Hz)', 'Theta (4–8 Hz)', 'Alpha (8–13 Hz)', 'Beta (13–30 Hz)', 'Gamma (30–100 Hz)']
    wave_colors = ['blue', 'purple', 'green', 'orange', 'red']
    lines = [axs[i].plot([], [], lw=2, color=wave_colors[i], label=wave_names[i])[0] for i in range(5)]

    # Configure each subplot
    for i, ax in enumerate(axs):
        ax.set_xlim(0, 100)  # Fixed x-axis range
        ax.set_ylim(-500, 500)  # Adjust y-axis range for EEG signal
        ax.legend(loc='upper right')
    plt.tight_layout()

    # Continuous streaming and plotting
    while True:
        data = board.get_current_board_data(100)  # Get last 100 samples
        # time.sleep(0.1)
        eeg_channels = board.get_eeg_channels(board_id)  # EEG channels
        if len(eeg_channels) > 0 and len(data) > 0:
            eeg_data = data[eeg_channels[0]]  # Use the first EEG channel

            # Filter data into bands
            delta = bandpass_filter(eeg_data, 0.5, 4, fs)
            theta = bandpass_filter(eeg_data, 4, 8, fs)
            alpha = bandpass_filter(eeg_data, 8, 13, fs)
            beta = bandpass_filter(eeg_data, 13, 30, fs)
            gamma = bandpass_filter(eeg_data, 30, 100, fs)

            # Update plots
            for line, band_data in zip(lines, [delta, theta, alpha, beta, gamma]):
                line.set_ydata(band_data)
                line.set_xdata(np.arange(len(band_data)))

            fig.canvas.draw_idle()
            fig.canvas.flush_events()

            # # Process EEG data
            print(f"EEG Data: {eeg_data}")
            print(f"Length of EEG Data: {len(eeg_data)}")

            abs_mean, max_peak = process_eeg_data(eeg_data)
            print(f"Processed EEG -> Mean: {abs_mean:.2f}, Peak: {max_peak:.2f}")

            # Calculate stimulation parameters
            ampl, durn, freq = calculate_stimulation_params(abs_mean, max_peak)
            print(f"Stimulation Params -> AMPL: {ampl}, DURN: {durn}, FREQ: {freq}")

            # Send stimulation commands to Arduino
            # Set parameters for Channel 1
            send_command(f"FREQ 1 {freq}")
            send_command(f"AMPL 1 {ampl}")
            send_command(f"DURN 1 {durn}")

            # Set parameters for Channel 2
            send_command(f"FREQ 2 {freq}")
            send_command(f"AMPL 2 {ampl}")
            send_command(f"DURN 2 {durn}")

            # Trigger stimulation for both channels
            send_command("STIM 1 10 0")
            send_command("STIM 2 10 0")

            time.sleep(6)  # Wait for stimulation to complete before the next cycle

except KeyboardInterrupt:
    print("\nStopping EEG Stream and Arduino Communication...")
    send_command("EOFF")  # Emergency stop stimulation
    board.stop_stream()
    board.release_session()
    arduino.close()
    plt.close()
