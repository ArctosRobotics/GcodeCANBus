import os
import tkinter as tk
from tkinter import ttk, filedialog
import time
import can
import serial.tools.list_ports
from convert import process_tap_files
from send import parse_can_message, adjust_speeds_within_packet, can_send_messages
from ttkthemes import ThemedStyle
import threading

# Global variables
selected_port = None
connected = False
bus = None
message_fields = [""] * 6  # Initialize message_fields
current_field_index = 0

# Function to refresh available ports
def refresh_ports():
    ports = [port.device for port in serial.tools.list_ports.comports()]
    port_combobox['values'] = ports
    port_combobox.current(0)  # Select the first port by default

# Function to connect to a selected port
def connect():
    global selected_port, connected, bus
    port = port_combobox.get()

    if not port:
        update_message("Please select a port.")
        return

    try:
        bus = can.interface.Bus(bustype="slcan", channel=port)
        connected = True
        selected_port = port
        connect_button.config(style='Green.TButton')  # Change button style to green upon successful connection
        update_message(f"Connected to port {port}.")
    except Exception as e:
        update_message(f"Error connecting: {str(e)}")

# Function to disconnect from the currently selected port
def disconnect():
    global connected, bus
    if connected:
        try:
            bus.shutdown()
            connected = False
            update_message(f"Disconnected from port {selected_port}.")
        except Exception as e:
            update_message(f"Error disconnecting: {str(e)}")
    else:
        update_message("Not connected to any port.")

# Function to send messages in a separate thread
def send_in_thread():
    global selected_port, connected, bus, current_field_index, message_fields

    if not connected:
        update_message("Not connected to any port.")
        return

    filename = send_file_entry.get()
    if not filename:
        update_message("Please select a file to send.")
        return

    try:
        with open(filename, "r") as file:
            for line in file:
                sent_message = line.strip()
                update_message(f"Sent: {sent_message}")

                # Parse the message and send it
                message = parse_can_message(sent_message)
                can_send_messages(bus, [message])

                # Extract 11th to 16th characters and convert from hex to decimal
                hex_values = sent_message[10:16]
                decimal_value = int(hex_values, 16) / 100  # Divide by 100
                decimal_value_formatted = "{:.2f}".format(decimal_value)  # Format to two decimal places

                # Append the decimal value to the current field
                message_fields[current_field_index] += f"{decimal_value_formatted}\n"
                current_field_index = (current_field_index + 1) % 6

                time.sleep(0.1)  # Sleep for a short duration to separate messages

                # Display messages in each field immediately
                for i, field_content in enumerate(message_fields, start=1):
                    field = field_widgets[field_labels[i-1].lower()]
                    field.config(state=tk.NORMAL, height=1)  # Set height to 1 line
                    field.delete('1.0', tk.END)
                    field.insert(tk.END, field_content)
                    field.config(state=tk.DISABLED)
                    # Update the GUI to immediately show the changes
                    root.update_idletasks()

        update_message("All messages sent successfully.")
    except Exception as e:
        update_message(f"Error sending messages: {str(e)}")

# Function to initiate sending messages
def send():
    threading.Thread(target=send_in_thread).start()

# Function to clear messages
def clear_messages():
    messages_text.config(state=tk.NORMAL)
    messages_text.delete('1.0', tk.END)
    messages_text.config(state=tk.DISABLED)

# Function to stop
def stop():
    # Placeholder for stopping logic
    pass

# Function to convert
def convert():
    input_filename = convert_file_entry.get()
    if not input_filename:
        update_message("Please select a file to convert.")
        return

    output_filename = os.path.splitext(input_filename)[0] + ".txt"
    try:
        process_tap_files()
        update_message(f"File converted successfully: {output_filename}")
    except Exception as e:
        update_message(f"Error converting file: {str(e)}")

# Function to handle file selection for conversion
def browse_convert_file():
    filename = filedialog.askopenfilename(filetypes=[("G-code files", "*.tap")])
    convert_file_entry.delete(0, tk.END)
    convert_file_entry.insert(0, filename)

# Function to handle file selection for sending
def browse_send_file():
    filename = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    send_file_entry.delete(0, tk.END)
    send_file_entry.insert(0, filename)

# Function to update messages
def update_message(message):
    messages_text.config(state=tk.NORMAL)
    messages_text.insert(tk.END, message + "\n")
    messages_text.config(state=tk.DISABLED)

# GUI setup
root = tk.Tk()
root.title("Arctos CAN controller")

# Create a themed style object
style = ThemedStyle(root)
style.set_theme("breeze")  # Set the theme to 'arc'

# Refresh button
refresh_button = ttk.Button(root, text="Refresh Ports", command=refresh_ports)
refresh_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

# Port selection dropdown
port_combobox = ttk.Combobox(root, width=25)
port_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

# Connect button
connect_button = ttk.Button(root, text="Connect", command=connect, style='Green.TButton')
connect_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

# Disconnect button
disconnect_button = ttk.Button(root, text="Disconnect", command=disconnect)
disconnect_button.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

# Send button (widest)
send_button = ttk.Button(root, text="Send", command=send, width=15)
send_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

# Convert button
convert_button = ttk.Button(root, text="Convert", command=convert)
convert_button.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

# Stop button
stop_button = ttk.Button(root, text="Stop", command=stop)
stop_button.grid(row=1, column=3, padx=5, pady=5, sticky="ew")

# File selection for conversion
convert_file_label = ttk.Label(root, text="Select File to Convert:")
convert_file_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")

convert_file_entry = ttk.Entry(root, width=30)
convert_file_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

convert_browse_button = ttk.Button(root, text="Browse", command=browse_convert_file)
convert_browse_button.grid(row=2, column=2, padx=5, pady=5, sticky="ew")

# File selection for sending
send_file_label = ttk.Label(root, text="Select File to Send:")
send_file_label.grid(row=3, column=0, padx=5, pady=5, sticky="e")

send_file_entry = ttk.Entry(root, width=30)
send_file_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

send_browse_button = ttk.Button(root, text="Browse", command=browse_send_file)
send_browse_button.grid(row=3, column=2, padx=5, pady=5, sticky="ew")

# Clear messages button (aligned with message display)
clear_button = ttk.Button(root, text="Clear Messages", command=clear_messages)
clear_button.grid(row=4, column=3, padx=5, pady=5, sticky="ew")

# Messages display
messages_label = ttk.Label(root, text="Messages:")
messages_label.grid(row=4, column=0, columnspan=3, padx=5, pady=(10, 0), sticky="w")

messages_text = tk.Text(root, height=8, width=50, state=tk.DISABLED)
messages_text.grid(row=5, column=0, columnspan=4, padx=5, pady=(0, 10), sticky="ew")

# Modify the labels for message fields
field_labels = ['X', 'Y', 'Z', 'A', 'B', 'C']

# Messages display fields
field_widgets = {}  # Dictionary to store references to text widgets

for i in range(6):
    # Create a frame for each label and text widget pair
    frame = ttk.Frame(root)
    frame.grid(row=i+6, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

    field_label = ttk.Label(frame, text=f"{field_labels[i]}:")
    field_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")

    field = tk.Text(frame, height=1, width=30, state=tk.DISABLED)
    field.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    # Store reference to the text widget in the dictionary
    field_widgets[field_labels[i].lower()] = field

root.mainloop()

