"""Browser boundary for a loopback-only, single-user demonstration."""
from urllib.parse import urlsplit
from starlette.responses import JSONResponse


class LocalOnlyMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)

        headers = {}
        for key, value in scope['headers']:
            headers.setdefault(key.lower(), []).append(value.decode('latin-1'))
        hosts = headers.get(b'host', [])
        valid_host = False
        if len(hosts) == 1:
            try:
                parsed = urlsplit('http://' + hosts[0])
                valid_host = (parsed.hostname in {'localhost', '127.0.0.1', '::1'}
                              and parsed.username is None and parsed.password is None
                              and not parsed.path and not parsed.query and not parsed.fragment)
                parsed.port  # Validate malformed or out-of-range ports as well.
            except ValueError:
                valid_host = False
        if not valid_host:
            return await JSONResponse({'detail': 'Host local requerido'}, status_code=400)(scope, receive, send)

        origins = headers.get(b'origin', [])
        expected = scope['scheme'] + '://' + hosts[0]
        cross_site = 'cross-site' in headers.get(b'sec-fetch-site', [])
        if cross_site or (origins and origins != [expected]):
            return await JSONResponse({'detail': 'Origen externo no permitido'}, status_code=403)(scope, receive, send)

        async def secure_send(message):
            if message['type'] == 'http.response.start':
                additions = [
                    (b'x-content-type-options', b'nosniff'),
                    (b'x-frame-options', b'DENY'),
                    (b'referrer-policy', b'no-referrer'),
                    (b'cache-control', b'no-store'),
                ]
                # Swagger has its own external assets; keep its existing renderer working.
                if scope['path'] == '/' or scope['path'].startswith('/static/'):
                    additions.append((b'content-security-policy',
                        b"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                        b"img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
                        b"base-uri 'none'; form-action 'self'; object-src 'none'"))
                names = {key for key, _ in additions}
                message['headers'] = [(key, value) for key, value in message.get('headers', [])
                                      if key.lower() not in names] + additions
            await send(message)

        await self.app(scope, receive, secure_send)
