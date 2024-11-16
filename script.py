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

# Low difficulty - 1
ampl_min = 5
ampl_max = 10
durn_min = 100
durn_max = 110

# Connect to Arduino
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
    eeg_values = np.array(eeg_data)
    abs_mean = np.mean(np.abs(eeg_values))
    max_peak = np.max(np.abs(eeg_values))
    return abs_mean, max_peak

def calculate_stimulation_params(abs_mean, max_peak):
    """Determine AMPL, DURN, and FREQ based on processed EEG data."""
    ampl = int(min(max(ampl_min, abs_mean * EEG_SCALING_FACTOR), ampl_max))  # Scale to 5-30 mA
    durn = int(min(max(durn_min, max_peak * EEG_SCALING_FACTOR), durn_max))  # Scale to 100-200 µs
    freq = 20 if abs_mean > EEG_THRESHOLD else 10  # Adjust frequency based on mean
    return ampl, durn, freq

def control_led(ampl, durn, ):
    """Determine which LED to light up based on AMPL and DURN."""
    led_value = ampl + durn  # Calculate LED value

    # Low difficulty 
    if 115 <= led_value <= 120:
        print(f"LED Control: Red (Value={led_value})")
        send_command("LED RED")
    elif 110 <= led_value < 115:
        print(f"LED Control: Yellow (Value={led_value})")
        send_command("LED YELLOW")
    elif 105 <= led_value < 110:
        print(f"LED Control: Green (Value={led_value})")
        send_command("LED GREEN")
    else:
        print(f"LED Control: Turn off (Value={led_value})")
        send_command("LED OFF")

# Muse 2 EEG Streaming Configuration
params = BrainFlowInputParams()
params.serial_port = 'COM14' 
board_id = 38  
fs = 256  

# Bandpass Filter Function
def bandpass_filter(data, lowcut, highcut, fs, order=4):
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

    for i, ax in enumerate(axs):
        ax.set_xlim(0, 100)
        ax.set_ylim(-500, 500)
        ax.legend(loc='upper right')
    plt.tight_layout()

    # Continuous streaming and plotting
    while True:
        data = board.get_current_board_data(100)
        eeg_channels = board.get_eeg_channels(board_id)
        if len(eeg_channels) > 0 and len(data) > 0:
            eeg_data = data[eeg_channels[0]]

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

            # Process EEG data
            abs_mean, max_peak = process_eeg_data(eeg_data)
            ampl, durn, freq = calculate_stimulation_params(abs_mean, max_peak)

            # Log stimulation parameters
            print(f"Stimulation Params -> AMPL: {ampl}, DURN: {durn}, FREQ: {freq}")

            # Control LEDs based on AMPL + DURN
            control_led(ampl, durn)

            # Send stimulation commands
            send_command(f"FREQ 1 {freq}")
            send_command(f"AMPL 1 {ampl}")
            send_command(f"DURN 1 {durn}")

            send_command(f"FREQ 2 {freq}")
            send_command(f"AMPL 2 {ampl}")
            send_command(f"DURN 2 {durn}")

            send_command("STIM 1 10 0")
            send_command("STIM 2 10 0")

            time.sleep(6)

except KeyboardInterrupt:
    print("\nStopping EEG Stream and Arduino Communication...")
    send_command("EOFF")
    board.stop_stream()
    board.release_session()
    arduino.close()
    plt.close()
