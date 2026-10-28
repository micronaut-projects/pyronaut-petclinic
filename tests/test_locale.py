"""Integration checks for locale."""



def test_locale_switch_matches_reference_cookie_and_redirect(client):
    response = client.get('/locale?lang=ES&backUrl=/owners/find', allow_redirects=False)
    assert response.status_code in (301, 302, 303)
    assert response.headers['location'].endswith('/owners/find')
    cookie = response.headers['set-cookie']
    assert 'locale=es' in cookie and 'httponly' in cookie.lower()
    assert 'Max-Age=31536000' in cookie
    spanish = client.get('/', headers={'Cookie': 'locale=es'})
    assert spanish.status_code == 200, spanish.text
    assert 'Bienvenido' in spanish.text
    assert '<html lang="es">' in spanish.text
    client.get('/locale?lang=de', allow_redirects=False)
    german = client.get('/')
    assert 'Willkommen' in german.text
    for target in ('https://example.com', '//example.com', '/locale?lang=es'):
        response = client.get('/locale', params={'lang': 'xx', 'backUrl': target}, allow_redirects=False)
        assert response.headers['location'] == '/'
        assert 'locale=en' in response.headers['set-cookie']
    # Restore the client's preference for the remaining tests.
    client.get('/locale?lang=en', allow_redirects=False)
