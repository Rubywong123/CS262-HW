# Logical Clock Synchronization Simulation

## Overview
This project simulates a distributed system where multiple virtual machines maintain logical clocks and exchange messages based on Lamport's logical clock algorithm. The simulation models the effects of different probabilities of internal events versus message exchanges on logical clock synchronization and message queue growth.

## Features
- Simulates multiple machines, each with an independent clock speed.
- Machines send messages to synchronize logical clocks and process internal events.
- Logs message exchanges, logical clock updates, and message queue sizes.
- Adjustable probability of sending messages versus processing internal events.
- Configurable number of machines and runtime duration.

## Installation & Usage
1. Clone the repository:
   ```bash
   git clone https://github.com/Rubywong123/CS262-HW.git
   cd HW3
   ```
2. Run the simulation with default settings (3 machines, 60 seconds runtime, 0.3 message-sending probability):
   ```bash
   python run.py
   ```
3. Customize the number of machines (default is 3):
   ```bash
   python run.py -- num_machines 4
   ```
4. Set the total simulation time (default is 60 seconds):
   ```bash
   python run.py -- time 80
   ```
5. Adjust the probability of sending messages (default is 0.3):
   ```bash
   python run.py -- send_message_prob 0.6
   ```

### Command-line Arguments
- `--num_machine`: Number of virtual machines in the simulation (default: 3).
- `--time`: Duration of the simulation in seconds (default: 60).
- `--send_message_prob`: Probability of sending a message instead of performing an internal event (default: 0.3).


## Log Output
Each machine logs its events to `logs/machine_<id>.log` with the format:
```
<timestamp> - Machine <id>: <event description> Message Queue Length: <length>
```

## Overall Observations
- Machines with higher clock speeds experience smaller jumps in logical clock values, while machines with slower clock speeds tend to have larger jumps due to less frequent updates.
- Machines with higher clock speeds exhibit greater drift in logical clock values and tend to have a higher logical clock value by the end of the experiment.
- Gaps in logical clock values occur when machines receive messages from much faster peers or when message processing lags due to bursts of incoming messages.
- When the variation in clock speeds among machines is smaller, the size of jumps in logical clock values is reduced, as machines synchronize more closely. This also leads to more stable message queue lengths. 
- With a higher probability of message sending, machines synchronize more frequently, resulting in smaller jumps in logical clock values. However, gaps in logical values may occur more frequently due to increased message exchanges.
- Message queue lengths may increase when messages are exchanged more frequently, especially if message processing cannot keep up with the rate of incoming messages.


## Tests
To run the tests and generate a coverage report, use the following command:

```bash
pytest --cov=. test_run.py
```
The test coverage for `run.py` is 65%. The primary reason for this coverage level is the extensive code within the `if __name__ == "__main__"` block, which is not directly tested. However, the test suite validates the core functionalities of the `VirtualMachine` and `Message` classes, including:

- **Message Serialization**: Ensures messages can be correctly serialized and deserialized.
- **Logical Clock Updates**: Verifies that messages are processed correctly and update the logical clock as expected.
- **Internal Events**: Confirms that internal events increment the logical clock properly.
- **Message Sending**: Tests sending messages to specific peers and broadcasting messages.
- **Message Queue Handling**: Checks that received messages are properly added to and processed from the queue.
- **Socket Communication**: Uses mocks to simulate network communication and validate expected interactions.
- **Integration Tests**: Includes a simple integration test to verify logical clock synchronization.
