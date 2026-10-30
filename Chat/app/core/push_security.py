"""Restrict outbound Web Push to browser-vendor services."""
from urllib.parse import urlsplit
from requests import Session


def validate_push_endpoint(value: str) -> str:
    try:
        url = urlsplit(value)
        host = url.hostname or ''
        allowed = host in {'fcm.googleapis.com', 'updates.push.services.mozilla.com', 'web.push.apple.com'}
        allowed = allowed or host.endswith('.push.services.mozilla.com') or host.endswith('.notify.windows.com')
        if (not allowed or url.scheme != 'https' or url.port not in (None, 443)
                or url.username is not None or url.password is not None or url.fragment
                or any(ord(char) <= 32 for char in value) or '\\' in value):
            raise ValueError('Unsupported push service endpoint')
    except (ValueError, TypeError):
        raise ValueError('Unsupported push service endpoint') from None
    return value


class PushSession(Session):
    def request(self, method, url, **kwargs):
        validate_push_endpoint(url)
        kwargs['allow_redirects'] = False
        return super().request(method, url, **kwargs)
