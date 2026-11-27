(() => {
    const form = document.getElementById('vet-edit-form');
    if (!form) return;

    const deleteForm = document.getElementById('vet-delete-form');
    const feedback = document.getElementById('vet-feedback');
    const message = document.getElementById('vet-feedback-message');
    const reload = document.getElementById('vet-reload');
    const isNew = form.dataset.isNew === 'true';
    let pending = false;

    function showFeedback(text, kind, needsReload = false) {
        message.textContent = text;
        feedback.className = 'alert alert-' + kind;
        feedback.hidden = false;
        if (reload) reload.hidden = !needsReload;
    }

    async function submit(submittedForm, deleting = false) {
        if (pending) return;
        if (deleting && !window.confirm(deleteForm.dataset.confirm)) return;

        const fields = new FormData(submittedForm);
        const specialityIds = fields.getAll('specialityIds').map(Number);
        let request;
        if (deleting) {
            request = {
                method: 'DELETE',
                headers: {'If-Match': '"' + fields.get('etag') + '"', 'Accept': 'application/json'}
            };
        } else if (isNew) {
            request = {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
                body: JSON.stringify({
                    firstName: fields.get('firstName'),
                    lastName: fields.get('lastName'),
                    specialityIds
                })
            };
        } else {
            request = {
                method: 'PUT',
                headers: {'Content-Type': 'application/json', 'Accept': 'application/json', 'If-Match': '"' + fields.get('etag') + '"'},
                body: JSON.stringify({
                    firstName: fields.get('firstName'),
                    lastName: fields.get('lastName'),
                    specialityIds
                })
            };
        }

        pending = true;
        const forms = deleteForm ? [form, deleteForm] : [form];
        const controls = forms.flatMap(currentForm => [...currentForm.elements]);
        const disabled = controls.map(control => control.disabled);
        controls.forEach(control => { control.disabled = true; });
        feedback.hidden = true;

        try {
            const response = await fetch(submittedForm.action, request);
            const body = deleting ? {} : await response.json().catch(() => ({}));
            if (!response.ok) {
                if (response.status === 412) {
                    showFeedback(feedback.dataset.conflict, 'warning', true);
                } else if (response.status === 428) {
                    showFeedback(feedback.dataset.missingEtag, 'warning', true);
                } else {
                    showFeedback(feedback.dataset.error, 'danger');
                }
                return;
            }
            if (deleting) {
                window.location.assign('/vets');
                return;
            }
            if (isNew) {
                if (!Number.isInteger(body.id)) {
                    showFeedback(feedback.dataset.error, 'danger');
                    return;
                }
                window.location.assign('/vets?saved=true');
                return;
            }
            if (!body.etag) {
                showFeedback(feedback.dataset.missingEtag, 'warning', true);
                return;
            }
            window.location.assign('/vets?saved=true');
        } catch (error) {
            showFeedback(feedback.dataset.networkError, 'danger');
        } finally {
            controls.forEach((control, index) => { control.disabled = disabled[index]; });
            pending = false;
        }
    }

    form.addEventListener('submit', event => {
        event.preventDefault();
        submit(form);
    });
    if (deleteForm) {
        deleteForm.addEventListener('submit', event => {
            event.preventDefault();
            submit(deleteForm, true);
        });
    }
})();
