from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


STATUS = [
    ('Activo', 'Activo'),
    ('Baja Provisional', 'Baja Provisional'),
    ('Baja Prov. Por Oficio', 'Baja Prov. Por Oficio'),
    ('Suspension Temporal', 'Suspension Temporal'),
    ('Baja Definitiva', 'Baja Definitiva'),
    ('Baja De Oficio', 'Baja De Oficio'),
    ('Baja Multiple Inscripcion', 'Baja Multiple Inscripcion'),
    ('Num Interno Identif', 'Num Interno Identif'),
    ('Otros Obligados', 'Otros Obligados')
]

CONDITION = [
    ('Habido', 'Habido'),
    ('No Hallado Se Mudo De Domicilio', 'No Hallado Se Mudo De Domicilio'),
    ('No Hallado Fallecio', 'No Hallado Fallecio'),
    ('No Hallado No Existe Domicilio', 'No Hallado No Existe Domicilio'),
    ('No Hallado Cerrado', 'No Hallado Cerrado'),
    ('No Hallado Nro.Puerta No Existe', 'No Hallado Nro.Puerta No Existe'),
    ('No Hallado Destinatario Desconocido', 'No Hallado Destinatario Desconocido'),
    ('No Hallado Rechazado', 'No Hallado Rechazado'),
    ('No Hallado Otros Motivos', 'No Hallado Otros Motivos'),
    ('Pendiente', 'Pendiente'),
    ('No Aplicable', 'No Aplicable'),
    ('Por Verificar', 'Por Verificar'),
    ('No Habido', 'No Habido'),
    ('No Hallado', 'No Hallado'),
    ('No Existe La Direccion Declarada', 'No Existe La Direccion Declarada'),
    ('Domicilio Cerrado', 'Domicilio Cerrado'),
    ('Negativa Recepcion X Persona Capaz', 'Negativa Recepcion X Persona Capaz'),
    ('Ausencia De Persona Capaz', 'Ausencia De Persona Capaz'),
    ('Devuelto', 'Devuelto')
]


class Partner(models.Model):
    _inherit = 'res.partner'

    economic_activity_ids = fields.One2many(
        'res.partner.economic.activity', 'partner_id', string='Actividades económicas')
    related_branch_ids = fields.One2many(
        'res.partner.related.branch', 'partner_id', string='Locales anexos')

    l10n_pe_taxpayer_type = fields.Char(string="Tipo de contribuyente")
    l10n_pe_trade_name = fields.Char(string="Nombre comercial")
    l10n_pe_registration_date = fields.Date(string="Fecha de inscripción")
    l10n_pe_activity_start_date = fields.Date(
        string="Fecha de inicio de actividades")
    l10n_pe_activity_end_date = fields.Date(string="Fecha de baja")

    l10n_pe_taxpayer_status = fields.Selection(
        STATUS, string='Estado del contribuyente')

    l10n_pe_taxpayer_condition = fields.Selection(
        CONDITION, string='Condicion')

    l10n_pe_invoice_emission_system = fields.Char(
        string="Sistema emisión de comprobante")
    l10n_pe_foreign_trade_activity = fields.Char(
        string="Actividad comercio exterior")
    l10n_pe_accounting_system = fields.Char(string="Sistema de contabilidad")
    l10n_pe_payment_receipt_authorized_printing = fields.Char(
        string="Comprobantes de pago c/aut. de impresión")
    l10n_pe_electronic_emission_system = fields.Char(
        string="Sistema de emisión electrónica")
    l10n_pe_electronic_emission_start_date = fields.Date(
        string="Emisor electrónico desde")
    l10n_pe_electronic_documents = fields.Char(
        string="Comprobantes electrónicos")
    l10n_pe_ple_affiliate_date = fields.Date(string="Afiliado al PLE desde")

    @api.model
    def default_get(self, fields_list):
        res = super(Partner, self).default_get(fields_list)
        res['l10n_latam_identification_type_id'] = self.env.ref(
            'l10n_pe.it_RUC').id
        res['country_id'] = self.env.ref('base.pe').id
        return res

    @api.onchange('l10n_latam_identification_type_id')
    def _onchange_l10n_latam_identification_type_id(self):
        doc_type = self.l10n_latam_identification_type_id.l10n_pe_vat_code
        if doc_type == "6":
            self.company_type = 'company'
        else:
            self.company_type = 'person'

    # TODO consulta buen contribuyente
    is_good_taxpayer = fields.Boolean(string="Buen contribuyente")

    repleg_identification_type = fields.Char(string='Documento')
    repleg_vat = fields.Char(string='Nro. de documento')
    repleg_start_date = fields.Date(string='Fecha desde')

    def _validate_pe_vat(self, vat, identification_type_id):
        """
        Valida si el RUC o DNI está escrito correctamente
        """
        it_RUC = self.env.ref('l10n_pe.it_RUC')
        it_DNI = self.env.ref('l10n_pe.it_DNI')
        if vat and int(identification_type_id) == it_DNI.id:
            if len(vat) != 8 or not vat.isdigit():
                raise ValidationError(
                    f'El DNI {vat} no es válido')
        if vat and int(identification_type_id) == it_RUC.id:
            if len(vat) != 11 or not vat.isdigit():
                raise ValidationError(
                    f'El RUC {vat} no es válido')
    
    def action_sunnat_connection_vat(self):
        """
        Llena los datos del contacto a partir del RUC o DNI
        Solo de los contactos generales, mas no de los contactos de la empresa
        """
        valid_partners = self.filtered(lambda r: not r.parent_id)
        for record in valid_partners:
            data = record.get_data_from_vat(
                record.vat, record.l10n_latam_identification_type_id.id)
            if data:
                record.write(data)
                
    @api.onchange('vat')
    def _onchange_vat(self):
        # Ayuda a que se pueda guardar el contacto sin digitar el nombre
        it_RUC = self.env.ref('l10n_pe.it_RUC')
        it_DNI = self.env.ref('l10n_pe.it_DNI')
        get_dni = self.env['ir.config_parameter'].sudo().get_param('sunat.get_data_from_dni')
        get_ruc = self.env['ir.config_parameter'].sudo().get_param('sunat.get_data_from_ruc')
        partner_identification_type_id = self.l10n_latam_identification_type_id.id
        if not self.name and self.vat:
            if (partner_identification_type_id == it_DNI.id and get_dni) or (partner_identification_type_id == it_RUC.id and get_ruc):
                self.name = self.vat
            
    @api.model_create_multi
    def create(self, vals_list):
        res = super(Partner, self).create(vals_list)
        res.action_sunnat_connection_vat()
        return res
    
    @api.model
    def get_data_from_vat(self, vat, identification_type_id):
        """
        Obtiene los datos del contacto a partir del RUC o DNI
        """
        self._validate_pe_vat(vat, identification_type_id)
        it_RUC = self.env.ref('l10n_pe.it_RUC')
        it_DNI = self.env.ref('l10n_pe.it_DNI')
        get_dni = self.env['ir.config_parameter'].sudo().get_param('sunat.get_data_from_dni')
        get_ruc = self.env['ir.config_parameter'].sudo().get_param('sunat.get_data_from_ruc')
        data = {}
        if vat and identification_type_id and int(identification_type_id) == it_DNI.id and get_dni:
            data = self._get_dni_data(vat)
        if vat and identification_type_id and int(identification_type_id) == it_RUC.id and get_ruc:
            data = self._get_ruc_data(vat)
        return data

    @api.model
    def _get_dni_data(self, dni):
        """
        Obtiene los datos del DNI
        """
        return {}

    @api.model
    def _get_ruc_data(self, ruc):
        """
        Obtiene los datos del RUC
        """
        return {}

    @api.model
    def _fetch_dni_raw_data(self, dni):
        """
        Obtiene los datos de un DNI en crudo
        """
        pass

    @api.model
    def _prepare_dni_data(self, response):
        """
        Sobreescribir este método para adaptar los datos del DNI a los campos del contacto
        """
        pass

    @api.model
    def _fetch_ruc_raw_data(self, ruc):
        """
        Obteniene los datos del RUC
        """
        pass
