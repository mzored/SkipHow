"""Offline privacy filtering for public receipts, without reading host accounts.

This removes recognized account metadata and common secret formats. It cannot
certify arbitrary prose as public; fixtures must still contain synthetic data.
"""

import hashlib
import json
import re


def _normalized(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.lower())


PRIVATE_FIELDS = frozenset({
    "ratelimitinfo", "ratelimittype", "unifiedwindows", "fivehour", "sevenday",
    "utilization", "resetsat", "isusingoverage", "overagestatus",
    "overagedisabledreason", "apikeysource", "accountid", "accountuuid",
    "organizationid", "organizationuuid", "orgid", "orguuid", "email",
    "emailaddress", "accesstoken", "refreshtoken", "idtoken", "apikey",
    "authorization", "cookie", "setcookie", "password", "clientsecret",
    "credentials", "authentication", "authprofile",
    "ratelimits", "ratelimitsbylimitid", "plantype", "account", "oauthaccount",
    "authmode",
})
SIGNATURE_OMITTED = "[host signature omitted]"
_UUID = re.compile(r"\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b", re.I)
_EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_HOME = re.compile(r"(?:/(?:Users|home)/[^/\s\"'<>\\]+|[A-Za-z]:[\\/]Users[\\/][^/\\\s\"'<>]+)")
_KEY = re.compile(r"\b(?:sk-(?:ant-|proj-)?[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16})\b")
_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
_BEARER = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]+=*", re.I)
_PEM = re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----[\s\S]*?(?:-----END (?:[A-Z]+ )?PRIVATE KEY-----|$)")
_ASSIGNMENT = re.compile(
    r"(?i)(\b(?:access[_-]?token|refresh[_-]?token|api[_-]?key|client[_-]?secret|password)\b\s*[:=]\s*)"
    r"(?:\"[^\"]*\"|'[^']*'|[^\s,;}]+)"
)


def _plain(text: str, redactions: dict[str, str]) -> str:
    for old in sorted(redactions, key=len, reverse=True):
        if not old or not redactions[old]:
            raise ValueError("redactions require nonempty literals and replacements")
        text = text.replace(old, redactions[old])
    text = _ASSIGNMENT.sub(lambda match: match[1] + '"<credential-omitted>"', text)
    for pattern in (_KEY, _JWT, _BEARER):
        text = pattern.sub("<credential-omitted>", text)
    text = _EMAIL.sub(lambda match: match[0] if match[0].lower().endswith("@example.invalid")
                     else "<email-omitted>", text)
    text = _HOME.sub("<operator-home>", text)
    return _UUID.sub(lambda match: "<trace-id-" + hashlib.sha256(
        match[0].lower().encode()).hexdigest()[:20] + ">", text)


def sanitize_text(text: str, redactions: dict[str, str] | None = None) -> str:
    """Preserve structured events, including JSON nested inside string values."""
    replacements = redactions or {}
    text = _PEM.sub("<private-key-omitted>", text)
    try:
        parsed = json.loads(text)
    except (ValueError, RecursionError):
        parsed = None
    else:
        clean = sanitize(parsed, replacements)
        if clean == parsed:
            return text
        return json.dumps(clean, ensure_ascii=False)
    text = _PEM.sub("<private-key-omitted>", text)
    lines = text.splitlines(keepends=True)
    if len(lines) > 1:
        output = []
        for line in lines:
            body = line.rstrip("\r\n")
            suffix = line[len(body):]
            output.append(sanitize_text(body, replacements) + suffix)
        return "".join(output)
    return _plain(text, replacements)


def sanitize(value: object, redactions: dict[str, str] | None = None) -> object:
    """Remove account fields and scrub values while retaining per-run usage."""
    if isinstance(value, str):
        return sanitize_text(value, redactions)
    if isinstance(value, list):
        return [sanitize(item, redactions) for item in value]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            normalized = _normalized(str(key))
            if normalized in PRIVATE_FIELDS:
                continue
            safe_key = _plain(str(key), redactions or {})
            if safe_key in result:
                raise ValueError("privacy filtering would merge distinct object fields")
            result[safe_key] = SIGNATURE_OMITTED if normalized == "signature" else sanitize(item, redactions)
        return result
    return value


def privacy_errors(value: object) -> list[str]:
    """Report locations and categories only, never source values or private keys."""
    errors = []

    def visit(item, path):
        if isinstance(item, dict):
            for index, (key, child) in enumerate(item.items()):
                normalized = _normalized(str(key))
                # A key can itself hold private text. Never echo arbitrary keys.
                location = f"{path}.field[{index}]"
                if normalized in PRIVATE_FIELDS:
                    errors.append(f"{location}: account or authentication field")
                elif normalized == "signature":
                    if child != SIGNATURE_OMITTED:
                        errors.append(f"{location}: host signature")
                else:
                    if _plain(str(key), {}) != str(key):
                        errors.append(f"{location}: private object key")
                    visit(child, location)
        elif isinstance(item, list):
            for index, child in enumerate(item):
                visit(child, f"{path}[{index}]")
        elif isinstance(item, str) and sanitize_text(item) != item:
            errors.append(f"{path}: private text or embedded metadata")

    visit(value, "$")
    return errors
