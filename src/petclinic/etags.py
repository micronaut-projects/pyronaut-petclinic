"""Reference speciality hash; row ETags are computed and checked by the database."""

from hashlib import sha256

EMPTY_SPECIALITIES_HASH = sha256(b'').hexdigest().upper()


def speciality_hash(ids) -> str:
    values = set(ids)
    if None in values:
        raise ValueError('ETag hashing requires specialities with persisted IDs.')
    return sha256(','.join(str(value) for value in sorted(values)).encode('utf-8')).hexdigest().upper()
