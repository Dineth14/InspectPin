"""Convert model output into plain technical English for speech synthesis."""

import re


_UNITS = {
    "MΩ": "megaohms", "kΩ": "kiloohms", "Ω": "ohms",
    "µF": "microfarads", "μF": "microfarads", "uF": "microfarads",
    "nF": "nanofarads", "pF": "picofarads",
    "mH": "millihenries", "µH": "microhenries", "μH": "microhenries", "uH": "microhenries",
    "kV": "kilovolts", "mV": "millivolts", "VAC": "volts A C", "VDC": "volts D C", "V": "volts",
    "mA": "milliamperes", "A": "amperes",
    "kW": "kilowatts", "mW": "milliwatts", "W": "watts",
    "GHz": "gigahertz", "MHz": "megahertz", "kHz": "kilohertz", "Hz": "hertz",
    "°C": "degrees Celsius", "°F": "degrees Fahrenheit", "%": "percent",
}
_UNIT_PATTERN = re.compile(
    r"(?<![\w.])([+-]?\d+(?:\.\d+)?)\s*("
    + "|".join(re.escape(unit) for unit in sorted(_UNITS, key=len, reverse=True))
    + r")(?![A-Za-zΩµμ])"
)
_DESIGNATORS = {
    "R": "resistor", "C": "capacitor", "L": "inductor", "D": "diode",
    "Q": "transistor", "F": "fuse", "J": "connector", "U": "integrated circuit",
    "K": "relay", "IC": "integrated circuit",
}


def normalize_for_speech(text: str) -> str:
    """Remove visual markup and expand common electronic notation for Piper."""
    value = str(text)
    value = re.sub(r"\[([^]]+)]\([^)]*\)", r"\1", value)
    value = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", value)
    value = re.sub(r"(?m)^\s*[-*+]\s+", ". ", value)
    value = value.replace("```", " ").replace("`", " ").replace("**", " ").replace("__", " ")
    value = _UNIT_PATTERN.sub(lambda m: f"{m.group(1)} {_UNITS[m.group(2)]}", value)
    value = re.sub(
        r"\b(IC|[RCLDQFJUK])(\d+)\b",
        lambda m: f"{_DESIGNATORS[m.group(1).upper()]} {m.group(2)}",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(r"#\s*(\d+)", r"number \1", value)
    value = value.replace("#", " ")
    value = value.replace("±", " plus or minus ").replace("×", " by ")
    value = value.replace("≤", " less than or equal to ").replace("≥", " greater than or equal to ")
    value = value.replace("≈", " approximately ").replace("=", " equals ")
    value = re.sub(r"(?<=\d)\s*/\s*(?=\d)", " or ", value)
    value = value.replace("&", " and ")
    value = re.sub(r"\s*\r?\n+\s*", ". ", value)
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"(?:\.\s*){2,}", ". ", value)
    return value.strip(" .") + "."
