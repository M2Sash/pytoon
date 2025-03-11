class JavaScript:
    @staticmethod
    def RGB2HEX(r, g, b):
        """Convert RGB values to a hex string."""
        return f'#{r:02x}{g:02x}{b:02x}'

    @staticmethod
    def HEX2RGB(hex_code):
        """Convert a hex string to RGB values."""
        hex_code = hex_code.lstrip('#')  # Remove the '#' if present
        if len(hex_code) != 6:
            raise ValueError("HEX code must be 6 characters long.")
        r = int(hex_code[0:2], 16)
        g = int(hex_code[2:4], 16)
        b = int(hex_code[4:6], 16)
        return r, g, b
