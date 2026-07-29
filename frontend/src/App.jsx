import React, {useEffect, useState} from 'react';
import {
  BrowserRouter, Link, Route, Routes, useLocation, useNavigate, useParams
} from 'react-router-dom';
import {StaticRouter} from 'react-router-dom/server';

const jsonHeaders = {'Content-Type': 'application/json'};

async function request(url, options = {}) {
  const response = await fetch(url, options);
  const body = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) {
    const error = new Error(body?.message || `Request failed (${response.status})`);
    error.status = response.status;
    error.errors = body?.errors || {};
    throw error;
  }
  return body;
}

function Layout({children}) {
  return <html lang="en">
    <head>
      <meta charSet="UTF-8"/>
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      <title>Pet Clinic</title>
      <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"/>
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"/>
      <link rel="stylesheet" href="/static/css/petclinic.css"/>
    </head>
    <body className="d-flex flex-column min-vh-100">
      <nav className="navbar navbar-expand-lg"><div className="container">
        <Link className="navbar-brand" to="/"><i className="fas fa-paw"/> Pet Clinic</Link>
        <div className="navbar-nav ms-auto">
          <Link className="nav-link" to="/">Home</Link>
          <Link className="nav-link" to="/owners/find">Find Owners</Link>
          <Link className="nav-link" to="/vets">Veterinarians</Link>
        </div>
      </div></nav>
      <main className="flex-grow-1 py-4">{children}</main>
      <footer className="footer"><div className="container text-center">
        <p className="mb-0">PetClinic · Pyronaut REST API + React</p>
      </div></footer>
    </body>
  </html>;
}

function Page({title, children, actions}) {
  return <div className="container">
    <div className="page-header d-flex justify-content-between align-items-center">
      <h1>{title}</h1>{actions}
    </div>
    {children}
  </div>;
}

function Welcome() {
  return <section className="hero"><div className="container hero-content text-center">
    <h1>Welcome to PetClinic</h1>
    <p>Care for pets, owners, visits, and veterinarians in one place.</p>
    <Link className="btn btn-outline-light btn-lg" to="/owners/find">Find an owner</Link>
  </div></section>;
}

function OwnerFind({initial}) {
  const [lastName, setLastName] = useState('');
  const navigate = useNavigate();
  function submit(event) {
    event.preventDefault();
    navigate(`/owners?lastName=${encodeURIComponent(lastName)}`);
  }
  return <Page title="Find Owners">
    {initial?.notFound && <div className="alert alert-warning">No owners found.</div>}
    <form className="card card-body" onSubmit={submit}>
      <label className="form-label" htmlFor="lastName">Last name</label>
      <input id="lastName" className="form-control" value={lastName} onChange={e => setLastName(e.target.value)}/>
      <div className="mt-3"><button className="btn btn-primary">Find Owner</button>{' '}
        <Link className="btn btn-success" to="/owners/new">Add Owner</Link></div>
    </form>
  </Page>;
}

function OwnerList({initial}) {
  const location = useLocation();
  const [state, setState] = useState({owners: initial?.owners, loading: !initial?.owners, error: null});
  useEffect(() => {
    if (initial?.owners) return;
    request(`/api/owners${location.search}`).then(owners => {
      if (owners.length === 1) window.location.assign(`/owners/${owners[0].id}`);
      else setState({owners, loading: false, error: null});
    }).catch(error => setState({owners: [], loading: false, error}));
  }, []);
  if (state.loading) return <Page title="Owners"><p>Loading…</p></Page>;
  if (state.error) return <ErrorMessage error={state.error}/>;
  return <Page title="Owners" actions={<Link className="btn btn-success" to="/owners/new">Add Owner</Link>}>
    {!state.owners.length ? <p>No owners found.</p> :
      <div className="row g-4">{state.owners.map(owner => <div className="col-md-6" key={owner.id}>
        <div className="card card-body"><h2><Link to={`/owners/${owner.id}`}>{owner.firstName} {owner.lastName}</Link></h2>
          <p>{owner.address}<br/>{owner.city}<br/>{owner.telephone}</p></div>
      </div>)}</div>}
  </Page>;
}

function OwnerDetail({initial}) {
  const {ownerId} = useParams();
  const [owner, setOwner] = useState(initial?.owner);
  const [error, setError] = useState(null);
  useEffect(() => {
    if (!owner) request(`/api/owners/${ownerId}`).then(setOwner).catch(setError);
  }, [ownerId]);
  if (error?.status === 404) return <NotFound message="Owner not found"/>;
  if (error) return <ErrorMessage error={error}/>;
  if (!owner) return <Page title="Owner"><p>Loading…</p></Page>;
  return <Page title={`${owner.firstName} ${owner.lastName}`} actions={<>
    <Link className="btn btn-primary" to={`/owners/${owner.id}/edit`}>Edit Owner</Link>{' '}
    <Link className="btn btn-success" to={`/owners/${owner.id}/pets/new`}>Add Pet</Link>
  </>}>
    <div className="card card-body mb-4"><p>{owner.address}<br/>{owner.city}<br/>{owner.telephone}</p></div>
    <h2>Pets and Visits</h2>
    {(owner.pets || []).map(pet => <div className="card card-body mb-3" key={pet.id}>
      <div className="d-flex justify-content-between"><h3>{pet.name} <small>{pet.type}</small></h3>
        <span><Link to={`/owners/${owner.id}/pets/${pet.id}/edit`}>Edit Pet</Link>{' · '}
          <Link to={`/owners/${owner.id}/pets/${pet.id}/visits/new`}>Add Visit</Link></span></div>
      <p>Born {pet.birthDate}</p>
      <div className="visit-timeline">{(pet.visits || []).map(visit =>
        <div className="visit-item" key={visit.id}><div className="visit-date">{visit.date}</div>
          <div className="visit-description">{visit.description}</div></div>)}</div>
    </div>)}
  </Page>;
}

const ownerFields = [
  ['firstName', 'First name'], ['lastName', 'Last name'], ['address', 'Address'],
  ['city', 'City'], ['telephone', 'Telephone']
];

function OwnerForm({initial}) {
  const {ownerId} = useParams();
  const isNew = initial?.isNew ?? !ownerId;
  const [form, setForm] = useState(initial?.owner || {});
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();
  useEffect(() => {
    if (!isNew && !form.id) request(`/api/owners/${ownerId}`).then(setForm);
  }, [ownerId]);
  async function submit(event) {
    event.preventDefault(); setSaving(true); setErrors({});
    try {
      const saved = await request(isNew ? '/api/owners' : `/api/owners/${ownerId}`, {
        method: isNew ? 'POST' : 'PUT', headers: jsonHeaders, body: JSON.stringify(form)
      });
      navigate(`/owners/${saved.id}`);
    } catch (error) { setErrors(error.errors); setSaving(false); }
  }
  return <Page title={isNew ? 'Add Owner' : 'Edit Owner'}><form className="card card-body" onSubmit={submit}>
    {ownerFields.map(([name, label]) => <Field key={name} name={name} label={label} value={form[name]}
      error={errors[name]} onChange={value => setForm({...form, [name]: value})}/>)}
    <button disabled={saving} className="btn btn-primary">{saving ? 'Saving…' : 'Save Owner'}</button>
  </form></Page>;
}

function PetForm({initial}) {
  const {ownerId, petId} = useParams();
  const isNew = initial?.isNew ?? !petId;
  const [form, setForm] = useState(initial?.pet || {});
  const [types, setTypes] = useState(initial?.types || []);
  const [errors, setErrors] = useState({});
  const navigate = useNavigate();
  useEffect(() => {
    if (!types.length) request('/api/pet-types').then(setTypes);
    if (!isNew && !form.id) request(`/api/owners/${ownerId}/pets/${petId}`).then(setForm);
  }, [ownerId, petId]);
  async function submit(event) {
    event.preventDefault(); setErrors({});
    try {
      await request(isNew ? `/api/owners/${ownerId}/pets` : `/api/owners/${ownerId}/pets/${petId}`, {
        method: isNew ? 'POST' : 'PUT', headers: jsonHeaders,
        body: JSON.stringify({...form, typeId: Number(form.typeId)})
      });
      navigate(`/owners/${ownerId}`);
    } catch (error) { setErrors(error.errors); }
  }
  return <Page title={isNew ? 'Add Pet' : 'Edit Pet'}><form className="card card-body" onSubmit={submit}>
    <Field name="name" label="Name" value={form.name} error={errors.name} onChange={value => setForm({...form, name: value})}/>
    <Field name="birthDate" label="Birth date" type="date" value={form.birthDate} error={errors.birthDate}
      onChange={value => setForm({...form, birthDate: value})}/>
    <label className="form-label" htmlFor="typeId">Type</label>
    <select id="typeId" className="form-select mb-3" value={form.typeId || ''} onChange={e => setForm({...form, typeId: e.target.value})}>
      <option value="">Choose a type</option>{types.map(type => <option key={type.id} value={type.id}>{type.name}</option>)}
    </select>{errors.typeId && <div className="text-danger">{errors.typeId}</div>}
    <button className="btn btn-primary">Save Pet</button>
  </form></Page>;
}

function VisitForm({initial}) {
  const {ownerId, petId} = useParams();
  const [form, setForm] = useState({});
  const [errors, setErrors] = useState({});
  const navigate = useNavigate();
  async function submit(event) {
    event.preventDefault(); setErrors({});
    try {
      await request(`/api/owners/${ownerId}/pets/${petId}/visits`, {
        method: 'POST', headers: jsonHeaders, body: JSON.stringify(form)
      });
      navigate(`/owners/${ownerId}`);
    } catch (error) { setErrors(error.errors); }
  }
  return <Page title={`Add Visit${initial?.pet?.name ? ` for ${initial.pet.name}` : ''}`}>
    <form className="card card-body" onSubmit={submit}>
      <Field name="date" label="Date" type="date" value={form.date} error={errors.date}
        onChange={value => setForm({...form, date: value})}/>
      <Field name="description" label="Description" value={form.description} error={errors.description}
        onChange={value => setForm({...form, description: value})}/>
      <button className="btn btn-primary">Add Visit</button>
    </form>
  </Page>;
}

function Vets({initial}) {
  const [vets, setVets] = useState(initial?.vets);
  const [error, setError] = useState(null);
  useEffect(() => { if (!vets) request('/api/vets').then(setVets).catch(setError); }, []);
  if (error) return <ErrorMessage error={error}/>;
  return <Page title="Veterinarians">{!vets ? <p>Loading…</p> :
    <div className="row g-4">{vets.map(vet => <div className="col-md-6" key={vet.id}>
      <div className="card card-body"><h2>{vet.firstName} {vet.lastName}</h2>
        <p>{vet.specialitiesAsString}</p></div></div>)}</div>}</Page>;
}

function Field({name, label, value = '', onChange, error, type = 'text'}) {
  return <div className="mb-3"><label className="form-label" htmlFor={name}>{label}</label>
    <input id={name} type={type} className={`form-control ${error ? 'is-invalid' : ''}`}
      value={value || ''} onChange={event => onChange(event.target.value)}/>
    {error && <div className="invalid-feedback">{error}</div>}</div>;
}

function ErrorMessage({error}) {
  return <Page title="Something went wrong"><div className="alert alert-danger">{error.message}</div></Page>;
}

function NotFound({message = 'Page not found'}) {
  return <Page title="404"><div className="alert alert-warning">{message}</div></Page>;
}

function RouteTree({page, data}) {
  const initial = name => page === name ? data : undefined;
  return <Layout><Routes>
    <Route path="/" element={<Welcome/>}/>
    <Route path="/owners/find" element={<OwnerFind initial={initial('ownerFind')}/>}/>
    <Route path="/owners" element={<OwnerList initial={initial('ownerList')}/>}/>
    <Route path="/owners/list" element={<OwnerList initial={initial('ownerList')}/>}/>
    <Route path="/owners/new" element={<OwnerForm initial={initial('ownerForm')}/>}/>
    <Route path="/owners/:ownerId" element={<OwnerDetail initial={initial('ownerDetail')}/>}/>
    <Route path="/owners/:ownerId/edit" element={<OwnerForm initial={initial('ownerForm')}/>}/>
    <Route path="/owners/:ownerId/pets/new" element={<PetForm initial={initial('petForm')}/>}/>
    <Route path="/owners/:ownerId/pets/:petId/edit" element={<PetForm initial={initial('petForm')}/>}/>
    <Route path="/owners/:ownerId/pets/:petId/visits/new" element={<VisitForm initial={initial('visitForm')}/>}/>
    <Route path="/vets" element={<Vets initial={initial('vets')}/>}/>
    <Route path="/vets/html" element={<Vets initial={initial('vets')}/>}/>
    <Route path="*" element={<NotFound message={initial('notFound')?.message}/>}/>
  </Routes></Layout>;
}

export function App({page, data, url}) {
  const content = <RouteTree page={page} data={data}/>;
  return url ? <StaticRouter location={url}>{content}</StaticRouter> : <BrowserRouter>{content}</BrowserRouter>;
}
