#!/usr/bin/env python3
#
# sym_highlighter.py

import re
from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.theme import Theme
from rich.color import Color, ANSI_COLOR_NAMES
from typing import Dict, Union

class SymHighlighter(RegexHighlighter):
    # Console default highlighter theme
    DEFAULT_STYLES = {
        "email": "yellow",
        "url": "green",
        "unix_path": "cyan",
        "windows_path": "#1e90ff",
        "ini": (255, 99, 71),
        "json": "#FFA500",
        "ipv4": "chartreuse2",
        "ipv6": "deep_pink3",
        "mac": "#9ACD32",
        "timestamp": "gold1",
        "hex_number": "#FF4500",
        "env_var": "magenta",
        "uuid": "sky_blue3",
        "datetime": "gold1",
        "phone_number": "turquoise4",
        "debug": "black",
    }  

    PHONE_PATTERNS = [
        r"(?P<phone_number>\+?\d{1,3}(-| |)?\(?\d{3}\)?(-| |)?\d{3}(-| |)?\d{4})",  # E.164 and variations
        r"(?P<phone_number>\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4})",  # Standard US formats
        r"(?P<phone_number>(\+|)\d{1,3}(-)\d{1,4}(-)\d{1,4}(-)\d{1,9})",  # International with optional separators
        r"(?P<phone_number>(\+|)\d{10})",  # Compact 10-digit
    ]

    DATETIME_PATTERNS = [
        r"(?P<datetime>\b\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?\b)",  # ISO-8601
        r"(?P<datetime>(?i:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday))",
        r"(?P<datetime>\b(?i:Mon|Tue(s)|Wed|Thu(rs)|Fri|Sat|Sun)\b)",
        r"(?P<datetime>(?i:January|February|March|April|May|June|July|August|September|October|November|December))",
        r'(?P<datetime>(?i:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))',
        r"(?P<datetime>\d{4}(/|-)(?:0[1-9]|1[0-2])(/|-)(?:0[1-9]|[12][0-9]|3[01])\b)",
        r"(?P<datetime>(?:[01][0-9]|2[0-3])(:)[0-5][0-9](:)(?:[0-5][0-9]|60)\b)",
        r"(?P<datetime>(?:[01][0-9]|2[0-3])(:)[0-5][0-9]\b)",
        r"(?P<datetime>\b(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}\b))",  # Standard datetime
        r"(?P<datetime>\b\d{2}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\b)",  # Special datetime
        r"(?P<datetime>(?:[01][0-9]|2[0-3])(:)[0-5][0-9]\b)",
        r"(?P<datetime>(?:(\d{2}){2}\d{4} (\d{2}:){3}))",
    ]

    NETWORK_PATTERNS = [
        r"\b(?P<ipv4>(?:(\d{1,3}\.){3}\d{1,3}(\/\d{1,2}\b|\/|)))",  # IPv4 pattern
        r"\b(?P<ipv6>(?:[0-9a-fA-F]{1,4}|)(:)([0-9a-fA-F]{1,4}))\b",
        r"\b(?P<ipv6>(?:[0-9a-fA-F]{1,4}))?!\.(\d{1,3}\.){3}",
        r"\b(?P<ipv6>(?:[0-9a-fA-F]{1,4}))?!.*::.*::",
        r"(?P<ipv6>(?:([0-9a-fA-F]{4}(:)[0-9a-fA-F]{3}(::))))",
        r"\b(?P<ipv6>(?:[0-9a-fA-F]{4}(::)))",
        r"(?P<ipv6>(?:(::|:)(([0-9a-fA-F]{4}+)|\d\b|([0-9a-fA-F]{3})(:)[0-9a-fA-F](::))))",
        r"(?P<mac>(?:(\s|^)([0-9a-fA-F]{2}(\.|\-|:)){5}[0-9a-fA-F]{2}))",
        r"(?P<mac>(?:(\s|^)[0-9a-fA-F]{12}))",
    ]

    MISC_PATTERNS = [
        r"(?P<unix_path>(?:[ \t\n]|^)/(?:[a-zA-Z0-9_.-]+/)*[a-zA-Z0-9_.-]+)",
        r"(?P<windows_path>([a-zA-Z]:\\|\\\\)[\w\\.-]+)",  # Windows file paths
        r"(?P<email>[\w.-]+@([\w-]+\.)+[\w-]+)",  # Email addresses
        r"(?P<url>([a-zA-Z]+):\/\/[a-zA-Z0-9\-._~:/?#[\]@!$&'()*+,;=%]+)",
        r"(?P<ini>\[\w+\])",                     # INI sections
        r"(?P<json>{.*?}|\[.*?\])",              # JSON-like objects
        r"(?P<hex_number>\b0x[0-9a-fA-F]+\b)",   # Hexadecimal numbers
        r"(?P<env_var>\$[\w]+|%[\w]+%)",         # Environment variables
        r"(?P<uuid>\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b)",  # UUIDs
    ]

    highlights = NETWORK_PATTERNS + PHONE_PATTERNS + DATETIME_PATTERNS + MISC_PATTERNS

    def __init__(self, styles: Dict[str, Union[str, tuple]] = None):
        """
        Initialize the highlighter with user-defined styles.

        Args:
            custtom_styles (Dict[str, Union[str, tuple]]): A dictionary mapping pattern names to colors.
                Colors can be strings (e.g., "red", "blue", "#RRGGBB") or RGB tuples.
        """
        if styles is None:
            styles = self.DEFAULT_STYLES

        self._validate_highlights()
        self.styles = self._convert_styles(styles)
        self.base_style = "highlight."
        super().__init__()

    def _validate_highlights(self):
        """Validate all regex patterns in the highlights list."""
        for pattern in self.highlights:
            try:
                re.compile(pattern)  # Attempt to compile the regex
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {pattern}\nError: {e}")

    def _convert_styles(self, styles: Dict[str, Union[str, tuple]]) -> Dict[str, str]:
        """Convert user-provided styles into rich-compatible color styles."""
        converted_styles = {}
        for key, color in styles.items():
            if isinstance(color, tuple):  # RGB tuple
                converted_styles[key] = Color.from_rgb(*color).name
            elif isinstance(color, str):  # Hex or named color
                if color.startswith("#"):  # Hex color
                    converted_styles[key] = Color.parse(color).name
                elif color in ANSI_COLOR_NAMES:  # Named color
                    converted_styles[key] = color
                else:
                    raise ValueError(f"Unsupported color name for '{key}': {color}. Must be a valid ANSI color.")
            else:
                raise ValueError(f"Unsupported color format for '{key}': {color}. Use named colors, hex, or RGB tuples.")
        return converted_styles

    def get_console(self) -> Console:
        """Return a rich.Console instance with the highlighter and custom theme."""
        return Console(highlighter=self, theme=self.theme)

    def debug_patterns(self, test_text: str):
        """Test all patterns against a given text and show matched groups."""
        for idx, pattern in enumerate(self.highlights, start=1):
            print(f"Pattern {idx}: {pattern}")
            matches = re.finditer(pattern, test_text)
            for match in matches:
                print(f"  Match: {match.groupdict()}\n")

    @property
    def theme(self) -> Theme:
        """Generate a rich Theme from the user-defined styles."""
        return Theme({f"highlight.{key}": value for key, value in self.styles.items()})

def main():
    # Test text
    test_text = """
    The server at 192.168.1.1/24 manages local network traffic, while the router gateway is set to 10.0.0.1. A public web server is accessible at 203.0.113.45, and an alternative testing server uses 198.51.100.27/32. For internal systems, we use a small subnet like 172.16.0.0/16. Occasionally, a device might have a static IP of 192.0.2.10, and legacy systems still refer to older IPs like 127.0.0.1 for loopback or 8.8.8.8 for Google's DNS. A customer mentioned their IP being 169.254.1.5, which falls under the link-local range. Lastly, our firewall monitors traffic from 123.123.123.123, a public IP on a different network.

    2001:db8:3333:4444:5555:6666:7777:8888
2001:db8:3333:4444:CCCC:DDDD:EEEE:FFFF
:: (implies all 8 segments are zero)
2001:db8:: (implies that the last six segments are zero)
::1234:5678
::2
  ::0bff:db8:1:1
       ::0bff:db8:1:1
  2001:db8::ff34:5678
  2001:db8::1:5678
2001:0db8:0001:0000:0000:0ab9:C0A8:0102 (This can be compressed to eliminate leading zeros, as follows: 2001:db8:1::ab9:C0A8:102 )
    Send funds to support@example.org
       AA:BB:CC:DD:EE:FF
aa:bb:cc:dd:ee:ff
Aa:Bb:Cc:Dd:Ee:Ff
AABBCCDDEEFF
        aabbccddeeff   
AaBbCcDdEeFf
AA-BB-CC-DD-EE-FF
aa-bb-cc-dd-ee-ff
Aa-Bb-Cc-Dd-Ee-Ff
AA.BB.CC.DD.EE.FF
aa.bb.cc.dd.ee.ff
Aa.Bb.Cc.Dd.Ee.Ff
IPv6: fe80::1ff:fe23:4567:890a
    IPv6: fe80::1ff:fe23:4567:890a
    Give me a call at 1234567890
    Visit https://example.com for more info.
    Check the config at /etc/config/settings.ini or C:\\Windows\\System32\\drivers\\etc\\hosts.
    My phone number is 942 282 1445 or 954 224-3454 or (282) 445-4983
    +1 (203) 553-3294 and this 1-849-933-9938 
    Here is some JSON: {"key": "value"} or an array: [1, 2, 3].
    IPv4: 192.168.1.1, IPv6: fe80::1ff:fe23:4567:890a, MAC: 00:1A:2B:3C:4D:5E.
    Timestamp: 2023-11-18T12:34:56Z, Hex: 0x1A2B3C, Env: $HOME or %APPDATA%.
    UUID: 550e8400-e29b-41d4-a716-446655440000
     https://localhost/test.html
    ssh://localhost:808/test
    11/19/2024 01:21:23
     11/19/2024 01:21:23
    12.03.24 
    Jan March May July dec 
    mon monday tues fri sunday
    IPv6: fe80::1ff:fe23:4567:890a
    Short: fe80::
    Dual: 2001:db8::192.168.1.1
    Invalid: 123::abc::456
    """
    print("Testing default")
    # test load default style highlights
    try:
        # Create a highlighter and console
        colors = SymHighlighter()
        console = colors.get_console()
        console.print(test_text)
    except ValueError as e:
        print(f"Error: {e}")

    #colors.debug_patterns(test_text)
    import sys
    sys.exit()

    print("Testing configured styles")
    # Define styles for highlighting
    test_styles = {
        "email": "yellow",
        "url": "green",
        "unix_path": "cyan",
        "windows_path": "#1E90FF",  # Dodger Blue
        "ini": (255, 99, 71),  # Tomato (RGB tuple)
        "json": "#FFA500",  # Orange
        "ipv4": "blue",  # Incorrect name will now raise an error
        "ipv6": "plum4",  # Adjusted color name
        "mac": "#9ACD32",  # YellowGreen
        "timestamp": "gold1",
        "hex_number": "#FF4500",  # OrangeRed
        "env_var": "magenta",
        "uuid": "gold1",  # Adjusted color name
    }

    try:
        # Create a highlighter and console
        custom = SymHighlighter(test_styles)
        console = Console(highlighter=custom, theme=custom.theme)

        console.print(test_text)
        del console
    except ValueError as e:
        print(f"Error: {e}")

    print("Testing for failure in styles")
    # Check failure of color types
    bad_styles = {
            "ipv4": "pink", # does not exist
    }

    try:
        # Create a highlighter and console
        custom = SymHighlighter(bad_styles)
        console = Console(highlighter=custom, theme=custom.theme)

        console.print(test_text)
        del console
    except ValueError as e:
        print(f"Error: {e}")

    '''
    highlighter = SymHighlighter()
    con = highlighter.get_console()

    con.print(test_text)

    highlighter.debug_patterns(test_text)
    '''


if __name__ == "__main__":
    main()

import re

# Mapping of strftime directives to regex patterns
STRFTIME_TO_REGEX = {
    "%A": r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)",
    "%a": r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)",
    "%B": r"(?:January|February|March|April|May|June|July|August|September|October|November|December)",
    "%b": r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)",
    "%C": r"\d{2}",  # Century
    "%c": r".+",  # Locale's date and time representation (complex)
    "%D": r"\d{2}/\d{2}/\d{2}",  # Equivalent to %m/%d/%y
    "%d": r"(?:0[1-9]|[12][0-9]|3[01])",  # Day of the month (01-31)
    "%e": r"(?: [1-9]|[12][0-9]|3[01])",  # Day of the month (1-31, space-padded)
    "%F": r"\d{4}-\d{2}-\d{2}",  # Equivalent to %Y-%m-%d
    "%G": r"\d{4}",  # ISO 8601 year with century
    "%g": r"\d{2}",  # ISO 8601 year without century
    "%H": r"(?:[01][0-9]|2[0-3])",  # Hour (00-23)
    "%h": r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)",  # Same as %b
    "%I": r"(?:0[1-9]|1[0-2])",  # Hour (01-12)
    "%j": r"(?:00[1-9]|0[1-9][0-9]|[12][0-9]{2}|3[0-6][0-6])",  # Day of year (001-366)
    "%k": r"(?: [0-9]|1[0-9]|2[0-3])",  # Hour (0-23, space-padded)
    "%l": r"(?: [1-9]|1[0-2])",  # Hour (1-12, space-padded)
    "%M": r"[0-5][0-9]",  # Minute (00-59)
    "%m": r"(?:0[1-9]|1[0-2])",  # Month (01-12)
    "%n": r"\n",  # Newline
    "%p": r"(?:AM|PM|am|pm)",  # Locale's AM/PM
    "%R": r"(?:[01][0-9]|2[0-3]):[0-5][0-9]",  # Equivalent to %H:%M
    "%r": r"(?:0[1-9]|1[0-2]):[0-5][0-9]:[0-5][0-9] (?:AM|PM|am|pm)",  # Equivalent to %I:%M:%S %p
    "%S": r"(?:[0-5][0-9]|60)",  # Second (00-60)
    "%s": r"\d+",  # Seconds since the Epoch
    "%T": r"(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]",  # Equivalent to %H:%M:%S
    "%t": r"\t",  # Tab
    "%U": r"(?:[0-4][0-9]|5[0-3])",  # Week number (Sunday-starting, 00-53)
    "%u": r"[1-7]",  # Weekday (1=Monday, 7=Sunday)
    "%V": r"(?:0[1-9]|[1-4][0-9]|5[0-3])",  # ISO 8601 week number (01-53)
    "%v": r"(?: [1-9]|[12][0-9]|3[01])-(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{4}",  # Equivalent to %e-%b-%Y
    "%W": r"(?:[0-4][0-9]|5[0-3])",  # Week number (Monday-starting, 00-53)
    "%w": r"[0-6]",  # Weekday (0=Sunday, 6=Saturday)
    "%X": r".+",  # Locale's time representation
    "%x": r".+",  # Locale's date representation
    "%Y": r"\d{4}",  # Year with century
    "%y": r"\d{2}",  # Year without century
    "%Z": r"[A-Za-z]+",  # Timezone name
    "%z": r"[+-]\d{4}",  # Timezone offset
    "%+": r".+",  # Locale's date and time representation
    "%%": r"%",  # Literal %
}
"""
class StrftimeRegex():
    def strftime_to_regex(patterns):
        new_pattern_list = []
        for pattern in patterns:
            # Match and process <datetime></datetime> tags
            def replace_strftime(match):
                inner_pattern = match.group(1)
                for strftime_directive, regex_equivalent in STRFTIME_TO_REGEX.items():
                    inner_pattern = inner_pattern.replace(strftime_directive, regex_equivalent)

                convert = f"(?P<datetime>{inner_pattern})"
                if re.compile(convert):
                    return convert

            # Replace all <datetime>...</datetime> tags with regex equivalents
            updated_pattern = re.sub(r"<datetime>(.*?)</datetime>", replace_strftime, pattern)
            new_pattern_list.append(updated_pattern)
        
        return new_pattern_list

    # Example usage
    patterns = [
        r"(?P<strftime>\b<datetime>%Y(/|.|-)%m(/|.|-)%d</datetime>\b)",
        r"(?P<strftime>\b<datetime>%H(:|.)%M(:|.)%S</datetime>\b)",
        r"(?P<strftime>\b<datetime>%H(:|.)%M</datetime>\b)",
        r"(?P<strftime>\b<datetime>%H(:|.)%M</datetime>\b)",
    ]

    converted_patterns = strftime_to_regex(patterns)
    for converted in converted_patterns:
        print(f"r\"{converted}\",")
"""
