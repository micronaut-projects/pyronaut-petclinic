"""Reference assignment hashes and H2's database ETag implementation."""

import pytest


def test_speciality_hash_sorts_ids_and_ignores_names_and_order():
    from petclinic.etags import speciality_hash
    from hashlib import sha256
    assert speciality_hash([3, 1, 3]) == speciality_hash([1, 3])
    assert speciality_hash([1, 3]) == sha256(b'1,3').hexdigest().upper()
    assert speciality_hash([1]) != speciality_hash([3])


def test_speciality_hash_empty_and_missing_ids():
    from petclinic.etags import EMPTY_SPECIALITIES_HASH, speciality_hash
    assert speciality_hash([]) == EMPTY_SPECIALITIES_HASH
    with pytest.raises(ValueError, match='persisted IDs'):
        speciality_hash([None])


def test_h2_row_etag_is_stable_and_covers_each_input():
    import java
    function = java.type('petclinic.VetEtagFunctions').sysRowEtag
    from petclinic.etags import EMPTY_SPECIALITIES_HASH
    tag = function(1, 'Sam', 'Lee', EMPTY_SPECIALITIES_HASH)
    assert len(tag) == 32 and all(c in '0123456789ABCDEF' for c in tag)
    assert tag == function(1, 'Sam', 'Lee', EMPTY_SPECIALITIES_HASH)
    for args in ((2, 'Sam', 'Lee', EMPTY_SPECIALITIES_HASH), (1, 'Pam', 'Lee', EMPTY_SPECIALITIES_HASH),
                 (1, 'Sam', 'Li', EMPTY_SPECIALITIES_HASH), (1, 'Sam', 'Lee', 'another-speciality-hash')):
        assert tag != function(*args)


def test_h2_row_etag_distinguishes_null_empty_and_field_boundaries():
    import java
    function = java.type('petclinic.VetEtagFunctions').sysRowEtag
    from petclinic.etags import EMPTY_SPECIALITIES_HASH as empty
    for left, right in (((1, None, 'Name', empty), (1, '', 'Name', empty)),
                        ((None, 'First', 'Last', empty), (0, 'First', 'Last', empty)),
                        ((1, 'ab', 'c', empty), (1, 'a', 'bc', empty)),
                        ((1, 'a:b', 'c', empty), (1, 'a', 'b:c', empty))):
        assert function(*left) != function(*right)
