import tkinter as tk

# Initial values for the parameters
amplMin = 0
amplMax = 0
durnMin = 0
durnMax = 0

#Colour parameters 
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
    global amplMin, amplMax, durnMin, durnMax

    if button_number == 1:
        amplMin, amplMax = 1, 10
        durnMin, durnMax = 1, 5
    elif button_number == 2:
        amplMin, amplMax = 10, 20
        durnMin, durnMax = 5, 10
    elif button_number == 3:
        amplMin, amplMax = 20, 30
        durnMin, durnMax = 10, 15
    elif button_number == 4:
        amplMin, amplMax = 30, 40
        durnMin, durnMax = 15, 20
    elif button_number == 5:
        amplMin, amplMax = 40, 50
        durnMin, durnMax = 20, 25

    # Update the labels or print the current values
    print(f"Button {button_number} clicked!")
    print(f"amplMin: {amplMin}, amplMax: {amplMax}")
    print(f"durnMin: {durnMin}, durnMax: {durnMax}")

    return amplMin, amplMax, durnMin, durnMax

# Create buttons numbered 1 to 5 and place them horizontally
button_frame = tk.Frame(root, background=bg)  # Create a frame to hold the buttons
button_colours = ["#6ad2e6","#ff6652", "#ffbbdc", "#51bd85", "#ffe534"]
for i in range(1, 6):
    button = tk.Button(button_frame, text=str(i), command=lambda i=i: on_button_click(i),font=button_font, bg=button_colours[i-1])
    button.pack(side="left", padx=5)  

button_frame.pack(pady=20)  

# Run the application
root.mainloop()
