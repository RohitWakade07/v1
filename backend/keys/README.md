# Instructor RSA private key (local development)

Place the instructor private key at:

```
keys/instructor_private.pem
```

This file is **gitignored** and must never be committed.

## Production (Railway / cloud)

Base64-encode the key and set `RSA_PRIVATE_KEY_B64`:

```bash
openssl base64 -A -in keys/instructor_private.pem
```

Leave `RSA_PRIVATE_KEY_B64` empty when using `RSA_PRIVATE_KEY_PATH` locally.
