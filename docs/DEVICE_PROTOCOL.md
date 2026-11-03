# Device protocol

## Identity and presence

Pairing creates a random per-device credential and stores only its hash. The
device sends its stable ID/token in headers. Heartbeats are expected every 30
seconds; the UI considers the device offline after 90 seconds. Battery percentage
is explicitly an estimate from the Li-Po voltage curve; charge state comes only
from valid charger-state hardware.

## Commands

The allow-list is `capture_photo`, `retry_upload`, `status`, `set_flashlight`,
`set_volume` and `vibrate`. Each command has an ID, expiry, status,
acknowledgement time and result. Devices poll rather than requiring a permanent
socket. Unsupported commands are rejected before persistence.

## Delivery and offline behavior

Captures have unique IDs and SHA-256 hashes. Chunk initialization and completion
are idempotent. Missing chunks and checksum mismatches do not publish an event.
Firmware retains original SD files and pending metadata; serial `r` retries one
item. Simulator offline/SD-removal modes exercise failure paths without claiming
physical behavior.
