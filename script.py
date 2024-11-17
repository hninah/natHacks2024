import serial
import time
import numpy as np
import matplotlib.pyplot as plt
from brainflow.board_shim import BoardShim, BrainFlowInputParams
from scipy.signal import butter, lfilter
# import settings 

# Configuration
COM_PORT = "COM13"  
BAUD_RATE = 115200  
EEG_THRESHOLD = 200  
EEG_SCALING_FACTOR = 0.02  

# Connect to Arduino
arduino = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
time.sleep(2) 
print("Connected to Arduino\n")

def send_command(command):
    """Send a command to the Arduino via serial."""
    arduino.write((command + "\r\n").encode()) 
    print(f"Sent to Arduino: {command}")
    time.sleep(0.1)  

def process_eeg_data(eeg_data):
    """Process EEG data to extract meaningful features."""
    eeg_values = np.array(eeg_data)
    abs_mean = np.mean(np.abs(eeg_values))
    max_peak = np.max(np.abs(eeg_values))
    return abs_mean, max_peak

def calculate_stimulation_params(abs_mean, max_peak, inital_avg):
    """Determine AMPL, DURN, and FREQ based on processed EEG data."""
    print(f"absolute mean: {abs_mean}")
    print(f"initial mean: {inital_avg}")

    if abs_mean < inital_avg + 50:
        print("ampl = 5")
        ampl = 10
        durn = 100
        send_command("LEDGREEN")
    if abs_mean > inital_avg + 50 and abs_mean < inital_avg + 100:
        print("ampl = 10")
        ampl = 15
        durn = 110
        send_command("LEDYELLOW")
    if abs_mean > inital_avg + 100:
        print("ampl = 20")
        ampl = 20
        durn = 120
        send_command("LEDRED")
    freq = 10
    return ampl, durn, freq

def control_led(ampl, durn, ):
    """Determine which LED to light up based on AMPL and DURN."""
    led_value = ampl + durn  # Calculate LED value

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
    data = board.get_current_board_data(100)
    eeg_channels = board.get_eeg_channels(board_id)
    eeg_data_initial = data[eeg_channels[0]]
    inital_avg, initial_peak = process_eeg_data(eeg_data_initial)
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
            ampl, durn, freq = calculate_stimulation_params(abs_mean, max_peak, inital_avg/2)

            # Log stimulation parameters
            print(f"Stimulation Params -> AMPL: {ampl}, DURN: {durn}, FREQ: {freq}")


            # Send stimulation commands
            send_command(f"FREQ 1 {freq}")
            send_command(f"AMPL 1 {ampl}")
            send_command(f"DURN 1 {durn}")

            send_command(f"FREQ 2 {freq}")
            send_command(f"AMPL 2 {ampl}")
            send_command(f"DURN 2 {durn}")

            send_command("STIM 1 10 0")
            send_command("STIM 2 10 0")

            control_led(ampl, durn)

            time.sleep(6)

except KeyboardInterrupt:
    print("\nStopping EEG Stream and Arduino Communication...")
    send_command(f"LEDOFF")
    board.stop_stream()
    board.release_session()
    arduino.close()
    plt.close()
