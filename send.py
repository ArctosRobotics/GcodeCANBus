import can
import os
import time

def parse_can_message(line):
    # Assuming each line in the file represents a CAN message in the format "ID DATA"
    parts = line.split(' ')
    arbitration_id = int(parts[0][:2], 16)
    data = [int(parts[0][i:i+2], 16) for i in range(2, len(parts[0]), 2)] + [int(byte, 16) for byte in parts[1:]]
    return can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=False)

def calculate_crc(arbitration_id, status):
    return (arbitration_id + 0xF4 + status) & 0xFF

def adjust_speeds_within_packet(messages):
    # Extract speeds from messages
    speeds = [(msg.data[3] << 8) + msg.data[4] for msg in messages]

    # Calculate reference speed as the average of all speeds
    reference_speed = sum(speeds) // len(speeds)

    # Check if the reference speed is zero
    if reference_speed == 0:
        return

    for msg in messages:
        speed = (msg.data[3] << 8) + msg.data[4]  # Extract the original speed
        adjusted_speed = int((speed / reference_speed) * reference_speed)
        
        msg.data[3] = (adjusted_speed >> 8) & 0xFF  # High byte of adjusted speed
        msg.data[4] = adjusted_speed & 0xFF  # Low byte of adjusted speed




def can_send_messages(bus, messages):
    expected_responses = {1, 2}  # IDs of motors expecting responses
    received_responses = set()

    for msg in messages:
        bus.send(msg)
        data_bytes = ', '.join([f'0x{byte:02X}' for byte in msg.data])
        print(f"Sent: arbitration_id=0x{msg.arbitration_id:X}, data=[{data_bytes}], is_extended_id=False")

    timeout = 0.5  # Increase the timeout value
    start_time = time.time()

    while True:
        # Receive a message
        received_msg = bus.recv(timeout=3)  # Adjust timeout as needed

        if received_msg is not None:
            # Print received messages for debugging
            received_data_bytes = ', '.join([f'0x{byte:02X}' for byte in received_msg.data])
            print(f"Received: arbitration_id=0x{received_msg.arbitration_id:X}, data=[{received_data_bytes}], is_extended_id=False")

            # Check if the received message is from an expected motor
            if received_msg.arbitration_id in expected_responses:
                received_responses.add(received_msg.arbitration_id)

        # Check if responses for all expected motors are received
        if received_responses == expected_responses:
            # Check if the status is 2 (run complete) for all received responses
            if all(received_msg.data[0] == 2 if received_msg is not None else False for received_msg in [bus.recv(timeout=0.1)] * len(expected_responses)):
                print("Responses received for all expected motors with status 2. Moving to the next set of messages.")
                break

        # Check if the timeout has elapsed
        if time.time() - start_time > timeout:
            print("Timeout waiting for responses from expected motors with status 2.")
            break

def main():
    script_directory = os.path.dirname(os.path.abspath(__file__))
    txt_files = [file for file in os.listdir(script_directory) if file.endswith(".txt")]

    if not txt_files:
        print("No .txt files found in the script directory.")
        return

    selected_file = txt_files[0]  # Assuming the first .txt file is the one to be used
    file_path = os.path.join(script_directory, selected_file)

    bus = can.interface.Bus(bustype='slcan', channel='/dev/ttyACM0', bitrate=500000)

    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Split the messages into sets of 6
    message_sets = [lines[i:i+6] for i in range(0, len(lines), 6)]

    for message_set in message_sets:
        messages = [parse_can_message(line.strip()) for line in message_set]

        # Adjust speeds within the packet based on positions
        adjust_speeds_within_packet(messages)

        can_send_messages(bus, messages)

    # Close the bus after sending all messages
    bus.shutdown()

if __name__ == "__main__":
    main()

