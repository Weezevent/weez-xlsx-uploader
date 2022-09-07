import time

from openpyxl import load_workbook

from .api import WeezeventApi, Tarifs, Forms


WEEZ_BULK_SIZE = 500


class XslxUploader:
    header_aliases = {
        'firstname': 'prenom',
        'first_name': 'prenom',
        'prénom': 'prenom',
        'lastname': 'nom',
        'last_name': 'nom',
        'barcode': 'barcode_id',
        'mail': 'email',
        'company': 'societe',
        'rate': 'tarif',
        'rate_name': 'tarif',
    }

    def __init__(self, path):
        self.wb = load_workbook(path)
        self.ws = self.wb.active
        self.headers, self.tickets = self.load_file()

    def load_file(self):
        headers = []
        tickets = []
        for i, row in enumerate(self.ws.rows):
            if i == 0:
                for cell in row:
                    headers.append(cell.value)
                headers = self.clean_headers(headers)
            else:
                ticket = {}
                for j, cell in enumerate(row):
                    ticket[headers[j]] = cell.value
                tickets.append(ticket)
        return headers, tickets

    def clean_headers(self, headers):
        headers = [h.strip().lower() for h in headers]
        headers = [self.header_aliases[h] if h in self.header_aliases else h for h in headers]
        return headers

    def prepare_event_config(self, *, api_key, username, password, event_id):
        """Ensure event is ready to welcome the tickets (Rates exists, Form exists...)"""
        self.api = WeezeventApi(api_key, username=username, password=password)
        self.event_id = event_id
        self.tarifs = Tarifs(self.api, event_id)

    def send(self):
        """Send the tickets to API"""
        to_push = []
        for ticket in self.tickets:
            tarif_id = self.tarifs.get_tarif(
                2179,
                ticket.get('tarif', 'WEEZ XLSX IMPORT'),
                ticket.get('tarif', 'WEEZ XLSX IMPORT'),
                0,
            )
            obj = {
                'id_evenement': self.event_id,
                'id_billet': tarif_id,
                'nom': ticket.get('nom', ''),
                'prenom': ticket.get('prenom', ''),
                'form': self.tarifs.map_form(tarif_id, ticket),
                'delete': False,
                'notify': False,
            }
            if ticket.get('barcode_id'):
                obj['barcode_id'] = ticket.get('barcode_id')
            if ticket.get('email'):
                obj['email'] = ticket.get('email')
            to_push.append(obj)

        if to_push:
            start_push = time.time()
            pushed = 0
            for i in range(int(len(to_push)/WEEZ_BULK_SIZE) + 1):
                chunk = to_push[i*WEEZ_BULK_SIZE:((i+1)*WEEZ_BULK_SIZE)]
                if len(chunk) > 0:
                    push_result = self.api.add_participants(
                        chunk,
                        unsafe_form=True,
                    )
                    pushed += push_result['total_added']

            end_push = time.time()
            print("pushed %s/%s participants in %s seconds" % (pushed, len(to_push), (end_push - start_push)))
