# unused_ports.py

Find unused switchports on Cisco Catalyst switches.

Intentionally opinionated and feature-poor ;) Use as a starting point for your own tooling.

By default, defines "unused" as any port that has not seen traffic for at least 1 week. Also verifies the switch has at least 1 week of uptime.

Uses a maximum of 50 SSH threads. Surprisingly fast while staying resource-efficient.

## Example usage

1. Rename `config.py.example` to `config.py` and match to your environment. If you don't have Solarwinds Orion NPM, you'll need to write your own inventory acquisition code (`get_devices()`)
1. Run `python3 unused_ports.py`

## Example output

All ports listed have not seen traffic for minimum cutoff (default 1 week).

```
switch1.example.net: [1, 3, 5, 7, 9, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48]
tor02.dc0.example.net: [1, 9, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48]
idf23.example.net: [3, 4, 6, 7, 8, 10, 12, 13, 14, 15, 16, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 2]
spine6.example.net: Device does not meet minimum uptime: 2 days, 7 hours, 17 minutes
access04.lax.example.net: [5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 19, 20, 21, 24, 25, 26, 27, 30, 31, 33, 35, 36, 37, 38, 39, 40, 44, 45, 47, 48]
idf42.example.net: [1, 4, 6, 7, 8, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 39, 41, 42, 47, 48]
switch2.example.net: [4, 8, 9, 10, 11, 12, 13, 14, 15, 16, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 36, 37, 38, 39, 40, 41, 42, 43, 44, 48]
tor10.dc1.example.net: Error connecting to device: Encountered EOF reading from transport; typically means the device closed the connection.
```
