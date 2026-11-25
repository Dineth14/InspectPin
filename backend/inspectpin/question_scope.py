"""Separate standalone spoken questions from follow-ups about the active photo."""
import re


_GENERAL_PREFIX = re.compile(
    r"^\s*(?:general question|without (?:using|looking at) (?:the |this )?(?:photo|image|picture))"
    r"(?:\s*[,.:;–—-]\s*|\s+)", re.IGNORECASE,
)
_PHOTO_REFERENCE = re.compile(
    r"\b(?:this|that|these|those|it|its|they|their|photo|picture|image|label|nameplate|"
    r"pictured|shown|visible|attached|above|here|left|right|see|read)\b", re.IGNORECASE,
)
_STANDALONE = re.compile(
    r"^\s*(?:what (?:is|are|does|do|causes)|how (?:does|do|can|should)|why (?:is|are|does|do)|"
    r"define|explain|describe|tell me about)\s+\S", re.IGNORECASE,
)
_PHOTO_PROPERTY = re.compile(
    r"^\s*(?:what (?:is|are) the |(?:describe|explain) the )"
    r"(?:voltage|current|power|resistance|capacitance|inductance|rating|value|serial|model|part number|"
    r"color|colour|marking|component|object|person|background|text|number|position|condition)\b",
    re.IGNORECASE,
)


def general_voice_question(transcript: str) -> str | None:
    """Return text for a standalone turn, or None when the photo stays in scope."""
    explicit = _GENERAL_PREFIX.match(transcript)
    if explicit and (question := transcript[explicit.end():].strip()):
        return question
    if (_STANDALONE.match(transcript) and not _PHOTO_REFERENCE.search(transcript)
            and not _PHOTO_PROPERTY.match(transcript)):
        return transcript
    return None
