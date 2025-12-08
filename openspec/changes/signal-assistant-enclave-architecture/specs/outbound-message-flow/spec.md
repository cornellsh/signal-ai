## ADDED Requirements

### Requirement: Enclave SHALL Encrypt LLM Response with Signal Protocol
The LLM-generated response, along with the recipient Signal ID, shall be encrypted by the enclave's Signal protocol stack using the appropriate Signal session keys.
#### Scenario: Enclave Prepares Outbound Message
Given the LLM has generated a response within the enclave,
When the enclave prepares to send this response to a user,
Then the enclave shall use its internal Signal protocol stack and the recipient's Signal session keys to encrypt the LLM-generated response.

### Requirement: Enclave SHALL Re-encrypt Signal Payload for Host Transport
The Signal-encrypted response shall then be re-encrypted by the enclave using the host-specific symmetric key for transport back to the host.
#### Scenario: Enclave Secures Payload for Host
Given the enclave has a Signal-encrypted response ready for dispatch,
When the enclave transfers this response to the host,
Then the enclave shall re-encrypt the Signal-encrypted payload using the pre-established host-enclave symmetric key,
And then send this host-encrypted payload to the host via an IPC mechanism.

### Requirement: Host SHALL Decrypt Enclave Transport Encryption
Upon receiving the host-encrypted Signal message from the enclave, the host shall decrypt it to retrieve the Signal-encrypted payload.
#### Scenario: Host Receives Enclave Response
Given the host receives a host-encrypted message from the enclave via IPC,
When the host processes this incoming payload,
Then the host shall successfully decrypt it using the pre-established host-enclave symmetric key,
And retrieve the original Signal-encrypted message payload.

### Requirement: Host SHALL Transmit Signal-Encrypted Message
The host shall transmit the Signal-encrypted message (obtained after decrypting the enclave transport encryption) to the Signal server for delivery to the user.
#### Scenario: Host Dispatches Message to Signal
Given the host has retrieved the Signal-encrypted message from the enclave,
When the host dispatches this message,
Then the host shall transmit the Signal-encrypted message to the Signal server,
And the host shall not decrypt or access the plaintext content of the Signal message.
