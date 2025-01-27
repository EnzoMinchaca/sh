from odoo.exceptions import ValidationError
from odoo import api, models, _
import requests
import re
from bs4 import BeautifulSoup

from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


URL = "https://e-consultaruc.sunat.gob.pe"

HEADERS = {
    'Host': 'e-consultaruc.sunat.gob.pe',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
    'sec-ch-ua-mobile': '?0',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
}


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _get_dni_data(self, dni):
        try:
            response = self._fetch_dni_raw_data(dni)
            data = self._prepare_dni_data(response)
        except Exception as e:
            data = {}
            _logger.warning(e)
        return data
    
    @api.model
    def _fetch_dni_raw_data(self, dni):
        """
        Obtiene los datos de un DNI en crudo
        """
        token = self.env['ir.config_parameter'].sudo().get_param('sunat.api_dni_token')
        #token = 'apis-token-9410.NokTsMWyA0gzNpFv3HfXyP54f3Pf1kNR'
        url = f'https://api.apis.net.pe/v2/reniec/dni?numero={dni}'
        headers = {
            'Accept': 'application/json',
            'Authorization': token, 
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            raise ValidationError(f'No se encontró el DNI {dni}')
        return response

    @api.model
    def _prepare_dni_data(self, response):
        raw_data = response.json()
        pre_data = {
            'names': raw_data.get('nombres', ''),
            'paternal_surname': raw_data.get('apellidoPaterno', ''),
            'maternal_surname': raw_data.get('apellidoMaterno', ''),
        }
        data = {
            'name': f"{pre_data['paternal_surname']} {pre_data['maternal_surname']} {pre_data['names']}",
        }
        return data
    
    @api.model
    def _get_ruc_data(self, ruc):
        """
        Prepara los datos completos del RUC
        """
        try:
            response_ruc, response_repleg, response_locanex = self._fetch_ruc_raw_data(ruc)
            ruc_data = self._get_raw_data_ruc_data(response_ruc)
            data = self._prepare_ruc(ruc_data)
            repleg = []
            locanex = []
            if response_repleg:
                repleg_data = self._get_raw_data_repleg_data(response_repleg)
                repleg = self._prepare_repleg(repleg_data)
            if response_locanex:
                locanex_data = self._get_raw_data_locanex_data(response_locanex)
                locanex = self._prepare_locanex(locanex_data)
            data['child_ids'] = repleg
            data['related_branch_ids'] = locanex
        except Exception as e:
            data = {}
            _logger.warning(e)
        return data

    @api.model
    def _fetch_ruc_raw_data(self, ruc):
        """
        Obteniene los datos del RUC
        """
        sesion = requests.Session()
        url = f"{URL}/cl-ti-itmrconsruc/jcrS00Alias"
        sesion = self._request_sesion_from_sunat_page(sesion)
        sesion, response = self._request_numRnd_from_sesion(sesion)
        response_ruc = self._request_ruc_data_from_numRnd(
            sesion, response, ruc)
        response_repleg = self._request_RepLeg_from_nroRuc(
            sesion, response_ruc, ruc)
        response_locanex = self._request_LocAnex_from_nroRuc(
            sesion, response_ruc, ruc)
        return response_ruc, response_repleg, response_locanex

    @api.model
    def _request_sesion_from_sunat_page(self, sesion):
        url = URL
        headers = HEADERS
        headers['Sec-Fetch-Site'] = 'none'
        sesion, response = self._request_from_sesion(
            sesion, "GET", headers, url)
        return sesion

    @api.model
    def _request_ruc_data_from_numRnd(self, sesion, response, ruc):
        soup = BeautifulSoup(response.text, "html.parser")
        numRnd = soup.find("input", {"name": "numRnd"})['value']
        url = f"{URL}/cl-ti-itmrconsruc/jcrS00Alias?accion=consPorRuc&nroRuc={ruc}&contexto=ti-it&modo=1&numRnd={numRnd}"
        headers = HEADERS
        headers['Referer'] = URL
        headers['Sec-Fetch-Site'] = 'same-origin'
        headers['Origin'] = URL
        sesion, response = self._request_from_sesion(
            sesion, "POST", headers, url)
        return response

    @api.model
    def _request_numRnd_from_sesion(self, sesion):
        headers = HEADERS
        headers['Referer'] = URL
        headers['Sec-Fetch-Site'] = 'same-origin'
        headers['Origin'] = URL
        headers['Upgrade-Insecure-Requests'] = '1'
        headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        numeroDNI = "12345678"
        url_dni = f"{URL}/cl-ti-itmrconsruc/jcrS00Alias?accion=consPorTipdoc&razSoc=&nroRuc=&nrodoc={numeroDNI}&contexto=ti-it&modo=1&search1=&rbtnTipo=2&tipdoc=1&search2={numeroDNI}&search3=&codigo="
        sesion, response = self._request_from_sesion(
            sesion, "POST", headers, url_dni)
        return sesion, response

    @api.model
    def _request_LocAnex_from_nroRuc(self,  sesion, response, ruc):
        if self.env['ir.config_parameter'].sudo().get_param('sunat.get_annexed_locals'):
            soup = BeautifulSoup(response.text, "html.parser")
            desRuc = soup.find("input", {"name": "desRuc"})['value']
            numRnd = soup.find("input", {"name": "numRnd"})['value']
            url = f"{URL}/cl-ti-itmrconsruc/jcrS00Alias?accion=getLocAnex&desRuc={desRuc}&nroRuc={ruc}&contexto=ti-it&modo=1&numRnd={numRnd}"
            headers = HEADERS
            headers['Origin'] = URL
            headers['Referer'] = url

            sesion, response = self._request_from_sesion(
                sesion, "POST", headers, url)
            return response

    @api.model
    def _request_RepLeg_from_nroRuc(self, sesion, response, ruc):
        if self.env['ir.config_parameter'].sudo().get_param('sunat.get_legal_representatives'):
            soup = BeautifulSoup(response.text, "html.parser")
            desRuc = soup.find("input", {"name": "desRuc"})['value']
            numRnd = soup.find("input", {"name": "numRnd"})['value']
            url = f"{URL}/cl-ti-itmrconsruc/jcrS00Alias?accion=getRepLeg&desRuc={desRuc}&nroRuc={ruc}&contexto=ti-it&modo=1&numRnd={numRnd}"
            headers = HEADERS
            headers['Origin'] = URL
            headers['Referer'] = url

            sesion, response = self._request_from_sesion(
                sesion, "POST", headers, url)
            return response

    @api.model
    def _request_from_sesion(self, sesion, method, headers, url):
        for i in range(15):
            response = sesion.request(
                method, url, headers=headers, verify=True)
            if response.status_code == 200:
                break
        if response.status_code != 200:
            raise ValidationError(
                f"No se pudo obtener los datos del RUC: {response.text}")
        return sesion, response

    @api.model
    def clean_value(self, value):
        value = value.strip()
        value = re.sub(r'\s+', ' ', value)
        value = value.replace('\n', '').replace('\r', '').replace('\t', '')
        value = value.title()
        return value

    @api.model
    def clean_key(self, key):
        key = key.replace('(', '').replace(')', '')
        key = key.title()
        key = key.replace('á', 'a').replace('é', 'e').replace(
            'í', 'i').replace('ó', 'o').replace('ú', 'u')
        key = re.sub(r'[^a-zA-Z]', '', key)
        return key

    @api.model
    def _get_raw_data_ruc_data(self, response):
        """
        Obtiene los datos del RUC en un diccionario a partir del contenido HTML
        """
        data = {}
        soup = BeautifulSoup(response.text, "html.parser")
        list_group_div = soup.find("div", class_="list-group")
        list_group_item_divs = list_group_div.find_all(
            'div', class_='list-group-item')

        for div in list_group_item_divs:
            h4_elements = div.find_all('h4', class_='list-group-item-heading')
            p_value_elements = div.find_all('p', class_='list-group-item-text')
            tbody_element = div.find('tbody')

            if len(h4_elements) == 2 and len(p_value_elements) == 0:
                key = self.clean_key(h4_elements[0].text)
                value = self.clean_value(h4_elements[1].text)
            elif len(h4_elements) == 2 and len(p_value_elements) == 2:
                for i in range(2):
                    key = self.clean_key(h4_elements[i].text)
                    value = self.clean_value(p_value_elements[i].text)
                    data[key] = value
            elif len(p_value_elements) == 1 and len(h4_elements) == 1:
                key = self.clean_key(h4_elements[0].text)
                value = self.clean_value(p_value_elements[0].text)
                if key == 'CondicionDelContribuyente':
                    condition = p_value_elements[0].contents[0]
                    value = self.clean_value(condition)
                elif key == 'EstadoDelContribuyente':
                    state = self.clean_value(p_value_elements[0].contents[0])
                    data[key] = state
                    if len(p_value_elements[0].contents) > 1 and len(p_value_elements[0].contents[1].split(':')) == 2:
                        key = 'FechaDeBaja'
                        end_date = p_value_elements[0].contents[1].split(':')[
                            1]
                        value = self.clean_value(end_date)

            elif tbody_element:
                key = self.clean_key(h4_elements[0].text)
                value = [self.clean_value(item.text)
                         for item in tbody_element.find_all("tr")]
            else:
                _logger.warning(f"Caso no contemplado: {div}")
                continue

            data[key] = value

        return data

    @api.model
    def _get_raw_data_repleg_data(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        repleg_data = []
        title_element = soup.find('title')
        if title_element.text not in [".:: Pagina de Error ::.", ".:: Pagina de Mensajes ::."]:
            table = soup.find('table')
            header_row = table.find('thead').find('tr')
            column_names = [header.text.strip()
                            for header in header_row.find_all('th')]

            # Iterar a través de las filas de la tabla (ignorando la primera fila de encabezado)
            for row in table.find_all('tr')[1:]:
                columns = row.find_all('td')
                representante = {}
                for i, column in enumerate(columns):
                    key = self.clean_key(column_names[i])
                    value = self.clean_value(column.text.strip())
                    representante[key] = value
                repleg_data.append(representante)

        return repleg_data

    @api.model
    def _convert_date(self, date_string):
        """
        Convierte una fecha en formato 'dd/mm/YYYY' a 'YYYY-mm-dd'
        """
        if date_string != '-':
            # '29/08/2022' Convierte a formato '2022-08-29'
            formated_date = datetime.strptime(
                date_string, '%d/%m/%Y').strftime('%Y-%m-%d')
        else:
            formated_date = False
        return formated_date

    def _prepare_ruc(self, data):
        def _get_activity_end_date(data):
            if 'FechaDeBaja' in data:
                activity_end_date = self._convert_date(data['FechaDeBaja'])
            else:
                activity_end_date = False
            return activity_end_date

        def _get_electronic_emission_system(data):
            if 'SistemaDeEmisionElectronica' in data:
                electronic_emission_system = ', '.join(
                    data['SistemaDeEmisionElectronica'])
            else:
                electronic_emission_system = False
            return electronic_emission_system
        
        def _get_economic_activity_data(economic_activities):
            activities = [(5, 0, 0)]
            for activity in economic_activities:
                type, code, _ = activity.split(' - ', 2)
                activity_id = self.env['l10n_pe.economic.activity'].search(
                    [('code', '=', code)], limit=1)
                if activity_id:
                    activities.append((0, 0, {
                        'partner_id': self.id,
                        'activity_type': type,
                        'l10n_pe_economic_activity_id': activity_id.id,
                    }))
            return activities

        def _get_location_data(full_address):
            parts = full_address.split(' - ')
            if len(parts) > 2:
                district, city, street_state = parts[-1], parts[-2], parts[-3]
                state = street_state.split()[-1]
                street = street_state.replace(state, '').strip()
            else:
                district, city, state, street = False, False, False, False
            if city == 'Prov. Const. Del Callao':
                district, city, state = 'Callao', 'Callao', 'Callao'

            return district, city, state, street

        name = data['NumeroDeRuc'].split(' - ')[1]
        country_id = self.env.ref('base.pe').id
        district, city, state, street = _get_location_data(
            data['DomicilioFiscal'])
        state_id = city_id = district_id = False

        if state:
            state_id = self.env['res.country.state'].search(
                [('name', 'ilike', state), ('country_id', '=', country_id)], limit=1)

        if city and state_id:
            city_id = self.env['res.city'].search(
                [('name', 'ilike', city), ('country_id', '=', country_id), ('state_id', '=', state_id.id)], limit=1)

        if district and city_id:
            district_id = self.env['l10n_pe.res.city.district'].search(
                [('name', 'ilike', district), ('city_id', '=', city_id.id)], limit=1)

        data = {
            'name': name.upper(),
            'country_id': country_id,
            'l10n_pe_district': district_id.id if district_id else False,
            'city_id': city_id.id if city_id else False,
            'state_id': state_id.id if state_id else False,
            'street': street,
            'city': city,
            'zip': district_id.code if district_id else False,
            'l10n_pe_taxpayer_type': data['TipoContribuyente'],
            'l10n_pe_trade_name': data['NombreComercial'],
            'l10n_pe_registration_date': self._convert_date(data['FechaDeInscripcion']),
            'l10n_pe_activity_start_date': self._convert_date(data['FechaDeInicioDeActividades']),
            'l10n_pe_taxpayer_status': data['EstadoDelContribuyente'],
            'l10n_pe_taxpayer_condition': data['CondicionDelContribuyente'],
            'l10n_pe_activity_end_date': _get_activity_end_date(data),
            'l10n_pe_invoice_emission_system': data['SistemaEmisionDeComprobante'],
            'l10n_pe_foreign_trade_activity': data['ActividadComercioExterior'],
            'l10n_pe_accounting_system': data['SistemaContabilidad'],
            'economic_activity_ids': _get_economic_activity_data(data['ActividadesEconomicas']),
            'l10n_pe_payment_receipt_authorized_printing': ', '.join(data['ComprobantesDePagoCAutDeImpresionFU']),
            'l10n_pe_electronic_emission_system': _get_electronic_emission_system(data),
            'l10n_pe_electronic_emission_start_date': self._convert_date(data['EmisorElectronicoDesde']),
            'l10n_pe_electronic_documents': data['ComprobantesElectronicos'],
            'l10n_pe_ple_affiliate_date': self._convert_date(data['AfiliadoAlPleDesde'])
        }
        
        return data

    def _prepare_repleg(self, raw_data):
        data = []
        for rep in raw_data:
            repleg = {
                'name': rep['Nombre'],
                'type': 'contact',
                'function': rep['Cargo'],
                'repleg_vat': rep['NroDocumento'],
                'repleg_start_date': self._convert_date(rep['FechaDesde']),
                'repleg_identification_type': rep['Documento'],
                'parent_id': self.id,
            }
            repleg_id = self.env['res.partner'].search(
                [('repleg_vat', '=', repleg['repleg_vat']), ('parent_id', '=', self.id)], limit=1)
            if repleg_id:
                data.append((1, repleg_id.id, repleg))
            else:
                data.append((0, 0, repleg))
        return data

    def _prepare_locanex(self, raw_data):
        data = []
        for loc in raw_data:
            locanex_economic_activity_id = self.env['l10n_pe.economic.activity'].search(
                [('code', '=', loc['ActividadEconomica'])], limit=1)
            locanex = {
                'code': loc['Codigo'],
                'branch_type': loc['TipoDeEstablecimiento'],
                'street': loc['Direccion'],
                'l10n_pe_economic_activity_id': locanex_economic_activity_id.id if locanex_economic_activity_id else False,
                'partner_id': self.id,
            }
            locanex_id = self.env['res.partner.related.branch'].search(
                [('code', '=', locanex['code']), ('partner_id', '=', self.id)], limit=1)
            if locanex_id:
                data.append((1, locanex_id.id, locanex))
            else:
                self.env['res.partner.related.branch'].create(locanex)
                data.append((0, 0, locanex))
        return data
    
    @api.model
    def _get_raw_data_locanex_data(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        locanex_data = []
        title_element = soup.find('title')
        if title_element.text not in [".:: Pagina de Error ::.", ".:: Pagina de Mensajes ::."]:
            list_group_div = soup.find("div", class_="list-group-item")
            table = list_group_div.find('table')
            header_row = table.find('thead').find('tr')
            column_names = [
                header.text for header in header_row.find_all('th')]

            body_rows = table.find('tbody').find_all('tr')
            for row in body_rows:
                columns = row.find_all('td')
                local = {}
                for i, column in enumerate(columns):
                    key = self.clean_key(column_names[i])
                    value = self.clean_value(column.text)
                    local[key] = value
                locanex_data.append(local)

        return locanex_data
