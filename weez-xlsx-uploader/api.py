import json

import requests


class WeezeventApiException(Exception):
    def __init__(self, message, type_, code, http_code):
        self.message = message
        self.type_ = type_
        self.code = code
        self.http_code = http_code

    def __str__(self):
        return "%s(message=%s, type=%s, code=%s, http_code=%s)" % (
            self.__class__.__name__, self.message, self.type_, self.code, self.http_code)


class ServerApiException(WeezeventApiException):
    def __init__(self, content, http_code):
        super().__init__(content, '', 0, http_code)


class PartialUpdateException(WeezeventApiException):
    def __init__(self, local_participants, extracted_participants, updated_participants):
        super().__init__(
            "Not all participants have been updated: %s/%s(%s)" % (
                updated_participants, local_participants, extracted_participants),
            None,
            None,
            200)


class WeezeventApi:
    access_token_url = '/auth/access_token'

    def __init__(self, api_key, *, access_token=None, username=None, password=None):
        self.url = "https://api.weezevent.com"
        self.api_key = api_key
        self.access_token = access_token
        self.session = requests.session()

        if username is not None and password is not None and access_token is None:
            self.get_access_token(username, password)

    def get_access_token(self, username, password, save=True):
        params = {'username': username, 'password': password, 'api_key': self.api_key}
        r = self.session.post(self.url + self.access_token_url, params=params)
        res = self.extract_response(r)
        access_token = self.extract_access_token(res)
        if save:
            self.access_token = access_token
        return access_token

    def extract_access_token(self, res):
        return res['accessToken']

    def extract_response(self, response):
        if response.status_code != 200:
            try:
                data = response.json()
                if 'error' in data:
                    data = data['error']
                raise WeezeventApiException(data['message'], data.get('type', ''), data['code'], response.status_code)
            except (ValueError, KeyError):
                raise ServerApiException(response.content, response.status_code)
        else:
            return response.json()

    def add_participants(self, participants, unsafe_form=False):
        params = {
            'access_token': self.access_token,
            'api_key': self.api_key,
            'data': json.dumps({
                'participants': participants,
                'return_ticket_url': 0,
                'unsafe_form': unsafe_form,
            })
        }
        r = self.session.post(self.url + '/v3/participants', data=params)
        return self.extract_response(r)

    def delete_participants(self, participants):
        params = {
            'access_token': self.access_token,
            'api_key': self.api_key,
            'data': json.dumps({
                'participants': participants,
            })
        }
        r = self.session.delete(self.url + '/v3/participants', data=params)
        return self.extract_response(r)

    def get_forms(self):
        params = {
            'access_token': self.access_token,
            'api_key': self.api_key,
        }
        r = self.session.get(self.url + '/v3/form', params=params)
        return self.extract_response(r)

    def add_form(self, form):
        params = {
            'access_token': self.access_token,
            'api_key': self.api_key,
            'data': json.dumps(form),
        }
        r = self.session.post(self.url + '/v3/form', data=params)
        return self.extract_response(r)

    def put_question(self, id_form, question):
        params = {
            'access_token': self.access_token,
            'api_key': self.api_key,
            'data': json.dumps(question),
        }
        r = self.session.put(self.url + f'/v3/form/{id_form}/question', data=params)
        return self.extract_response(r)

    def get_tarifs(self, id_event):
        params = {
            'access_token': self.access_token,
            'api_key': self.api_key,
        }
        r = self.session.get(self.url + '/v3/evenement/' + str(id_event) + '/tarifs', params=params)
        return self.extract_response(r)

    def add_tarif(self, id_event, ticket):
        """
        :param id_event: event where the tarif must be created
        :param ticket: dict object example: {'name': 'My first tarif'}, get one ticket to know the other fields
        :return: ticket object after creation
        """
        params = {
            'data': json.dumps(ticket),
            'access_token': self.access_token,
            'api_key': self.api_key,
        }
        r = self.session.post(self.url + '/v3/evenement/' + str(id_event) + '/tarifs', data=params)
        return self.extract_response(r)


class Form:

    DEFAULT_FIELD = """adresse
adressedelivraison
adresse_societe
billet_prix
blog
choix_place
civilite
codepostaldelivraison
code_postal
code_postal_societe
commentaires
date_de_naissance
email
email_pro
fonction
nom
pays
paysdelivraison
pays_societe
portable
portable_societe
prenom
site_internet
societe
telephone
validity_date_start
ville
villedelivraison
ville_societe""".split('\n')

    def __init__(self, forms, form):
        self.api = forms.weezevent_api
        self.forms = forms
        self.form = form

    def get_key_for_label(self, label):
        for question in self.questions:
            if question.get('label') == label:
                return question['id']

        q = self.put_question(label)
        return q['id']

    def put_question(self, label):
        q = self.api.put_question(self.id_form, {
            "type": "custom",
            "label": label,
            "field_type": "textfield",
            "buyer": 0,
            "bo_only": 1,
        })
        self.form['questions_participant'].append(q)
        return q

    @property
    def id_form(self):
        return self.form['id_form']

    @property
    def questions(self):
        return self.form['questions_participant']

    @property
    def tickets(self):
        return self.form['tickets']


class Forms:
    def __init__(self, weezevent_api, id_event):
        self.weezevent_api = weezevent_api
        self.id_event = id_event

        forms = self.get_forms()
        self.forms = {}
        self.forms_by_billet_id = {}
        for f in forms:
            form = Form(self, f)
            self.forms[f['id_form']] = form
            for billet_id in form.tickets:
                self.forms_by_billet_id[billet_id] = form

    def get_forms(self):
        return [
            form for form in self.weezevent_api.get_forms()
            if form['id_evenement'] == str(self.id_event)
        ]

    def add_form_for_id_billet(self, id_billet):
        f = self.weezevent_api.add_form({
            'id_evenement': self.id_event,
            'title': f'Form for {id_billet}',
            'questions_buyer': [],
            'questions_participant': [],
            'tickets': [id_billet],
        })
        form = Form(self, f)
        self.forms_by_billet_id[id_billet] = form
        self.forms[f['id_form']] = form


class Tarifs:
    def __init__(self, weezevent_api, id_event):
        self.weezevent_api = weezevent_api
        self.id_event = id_event

        tarifs = self.get_tarifs()
        self.tarifs_mapping = {}
        for t in tarifs:
            key = t.get('id_code_distrib', '')
            if key:
                self.tarifs_mapping[str(t['channel_id']) + ':::' + key] = t

        self.forms = Forms(weezevent_api, id_event)

    def add_tarif(self, channel_id, id_distributor, name, price, id_categorie=None, description=''):
        key = str(channel_id) + ':::' + str(id_distributor)
        tarif = self.weezevent_api.add_tarif(self.id_event, {
            'nom': name,
            'description': description,
            'id_code_distrib': id_distributor,
            'prix': price,
            'channel_id': channel_id,
            'id_categorie': id_categorie})
        self.tarifs_mapping[key] = tarif
        return tarif['id_billet']

    def get_tarif(self, channel_id, id_distributor, name, price, id_categorie=None, description=''):
        key = str(channel_id) + ':::' + str(id_distributor)
        if id_categorie is None:
            id_categorie = 0
        if key not in self.tarifs_mapping:
            self.add_tarif(channel_id, id_distributor, name, price, id_categorie, description)
        else:
            # TODO handle update ?
            pass
        return self.tarifs_mapping[key]['id_billet']

    def get_tarifs(self):
        return self.weezevent_api.get_tarifs(self.id_event)

    def patch_tarif(self, tarif):
        return self.weezevent_api.patch_tarif(self.id_event, tarif['id_billet'], tarif)

    def map_form(self, id_billet, form):
        id_billet = str(id_billet)
        # Take a dict of key-value, and transform it to be passed as form in attendee API
        result_form = {}
        form_obj = self.forms.forms_by_billet_id.get(id_billet)
        for key, value in form.items():
            if key in Form.DEFAULT_FIELD:
                result_form[key] = value
                continue

            if form_obj is None:
                self.forms.add_form_for_id_billet(id_billet)
                form_obj = self.forms.forms_by_billet_id.get(id_billet)

            result_form[form_obj.get_key_for_label(key)] = value
        return result_form
