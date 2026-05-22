from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
}

GOOGLE_REDIRECT_PARAMS = ("url", "q", "u")


def normalize_url(url: str) -> str:
    if not url:
        return ""

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return url

    target_url = _extract_google_redirect_target(parsed)
    if target_url:
        return normalize_url(target_url)

    query = urlencode(
        [
            (key, value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
            if key.lower() not in TRACKING_PARAMS
        ],
        doseq=True,
    )
    path = parsed.path
    if path != "/":
        path = path.rstrip("/")

    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            path,
            parsed.params,
            query,
            parsed.fragment,
        )
    )


def _extract_google_redirect_target(parsed_url) -> str:
    hostname = parsed_url.netloc.lower()
    if not hostname.endswith("google.com"):
        return ""

    query_params = dict(parse_qsl(parsed_url.query, keep_blank_values=True))
    for param in GOOGLE_REDIRECT_PARAMS:
        target_url = query_params.get(param)
        if target_url and urlparse(target_url).scheme in {"http", "https"}:
            return target_url

    return ""
