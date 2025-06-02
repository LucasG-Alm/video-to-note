def print_hex_color(hex_color, msg, msg2=""):
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    print(f"\033[38;2;{r};{g};{b}m{msg}\033[0m {msg2}")

