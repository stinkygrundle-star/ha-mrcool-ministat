DOMAIN = "mrcool_ministat"
CMD_CHAR = "0000ffe9-0000-1000-8000-00805f9b34fb"
NOTIFY_CHAR = "0000ffe4-0000-1000-8000-00805f9b34fb"
FD02_CHAR = "0000fd02-0000-1000-8000-00805f9b34fb"
POLL_SECONDS = 60

# Command: TTM(AS,K P M TT F S 00000000)
# K = key pressed: 0 normal, 1 FP, 2 turbo toggle, 3 swing (P=1 toggle, P=0 louver step),
#     5 LED toggle, 6 follow-me toggle
KEY_NORMAL, KEY_FP, KEY_TURBO, KEY_SWING, KEY_LED, KEY_FOLLOW = "0", "1", "2", "3", "5", "6"
# M = mode
MODE_AUTO, MODE_COOL, MODE_DRY, MODE_FAN, MODE_HEAT, MODE_FP = "0", "1", "2", "3", "4", "5"
# F = fan
FANS = {"auto": "0", "low": "1", "medium": "2", "high": "3"}
