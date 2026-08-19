## ID: BLE-03

## Title: Bluetooth connection distance/reconnection test.

## Preconditions:
- software running
- cube connected to software

## Steps:
1. With cube connected, confirm connection and input functions first.
2. Take cube and walk away from bluetooth connection source (PC) a few steps at a time, pausing for 5-10 seconds each time.
3. monitor connection on PC (may require a second QA member) as distance increases.
4. note rough estimate of distance that cube loses connection.
5. return towards PC and see if software attempts to reconnect automatically. If not, reconnect manually. note if success or failure.

## Expected Result:
cube remains connected to PC up to a distance of 10-15 feet, or standard bluetooth connection range, then disconnects. Automatic reconnection is not currently a known feature, manual reconnection likely necessary.

## Related Issue(s):
none
