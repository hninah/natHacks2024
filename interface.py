import tkinter as tk
import settings  

# Colour parameters 
large_font = ("Arial", 24)  
button_font = ("Arial", 20)
bg = "#fffff0"
text = "black"

# Create the main window
root = tk.Tk()
root.title("Muse Helper")
root.config(bg=bg)


# Add labels for user messages
message1 = tk.Label(
    text="Hello, User",
    foreground=text, 
    background=bg,
    font=large_font
)
message1.pack(pady=10)

message2 = tk.Label(
    text="Choose intensity: 1 (low) - 5 (high)",
    foreground=text, 
    background=bg,
    font=large_font
)
message2.pack(pady=10)

# Function to handle button click events and update parameters
def on_button_click(button_number):
    if button_number == 1:
        settings.amplMin, settings.amplMax = 1, 10
        settings.durnMin, settings.durnMax = 1, 5
    elif button_number == 2:
        settings.amplMin, settings.amplMax = 10, 20
        settings.durnMin, settings.durnMax = 5, 10
    elif button_number == 3:
        settings.amplMin, settings.amplMax = 20, 30
        settings.durnMin, settings.durnMax = 10, 15
    elif button_number == 4:
        settings.amplMin, settings.amplMax = 30, 40
        settings.durnMin, settings.durnMax = 15, 20
    elif button_number == 5:
        settings.amplMin, settings.amplMax = 40, 50
        settings.durnMin, settings.durnMax = 20, 25

    print(settings.amplMax)

# Create buttons numbered 1 to 5 and place them horizontally
button_frame = tk.Frame(root, background=bg)  # Create a frame to hold the buttons
button_colours = ["#6ad2e6","#ff6652", "#ffbbdc", "#51bd85", "#ffe534"]
for i in range(1, 6):
    button = tk.Button(button_frame, text=str(i), command=lambda i=i: on_button_click(i), font=button_font, bg=button_colours[i-1])
    button.pack(side="left", padx=5, expand=True)  

button_frame.pack(pady=20)  

# Run the application
root.mainloop()  
