"""Integration checks for application."""



def test_application_starts(application_context):
    """The embedded server is available from the Micronaut context."""

    assert application_context.isRunning()


def test_seed_data_and_main_pages(client):
    assert "Welcome" in client.get("/").text
    css = client.get("/resources/css/petclinic.css")
    assert css.status_code == 200
    assert "text/css" in css.headers["content-type"]
    assert ".navbar" in css.text
    vets = client.get("/vets/json").json()
    assert len(vets) == 6
    assert any(vet["lastName"] == "Douglas" for vet in vets)
    vet_page = client.get("/vets").text
    assert "dentistry" in vet_page and "surgery" in vet_page
    owners = client.get("/owners/list").text
    assert "George Franklin" in owners
    assert "Betty Davis" in owners


def test_jinjava_templates_render_inheritance_and_conditionals(client):
    """Jinjava renders the shared layout and Jinja control flow."""

    owners = client.get("/owners/list")
    assert owners.status_code == 200
    assert "Pet Clinic" in owners.text
    assert "George Franklin" in owners.text
    assert "$owner_count" not in owners.text
    assert "{%" not in owners.text

    not_found = client.get("/owners/list?lastName=DoesNotExist")
    assert not_found.status_code == 200
    assert "No Owners Found" in not_found.text
