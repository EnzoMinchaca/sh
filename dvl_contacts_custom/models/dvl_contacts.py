from odoo import api, models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    data_line_ids = fields.One2many('data.line', 'partner_id', string='Datos', store=True)

    contact_line_ids = fields.One2many('contact.line', 'partner_id', string='Contactos', store=True)

    ubicacion_line_ids = fields.One2many('ubicacion.line', 'partner_id', string='Ubicación', store=True)

    accesos_line_ids = fields.One2many('accesos.line', 'partner_id', string='Accesos', store=True)

    @api.onchange('data_line_ids')
    def _onchange_data_lines(self):
        print("onchange data lines")
        if self.data_line_ids:
            # Ordenar data_line_ids por sequence
            sorted_lines = sorted(self.data_line_ids, key=lambda line: line.sequence)
            if sorted_lines:
                self.vat = sorted_lines[0].ruc
                print('self.vat', self.vat)
            
    @api.onchange('contact_line_ids')
    def _onchange_contact_lines(self):
        print("onchange contact lines")
        if self.contact_line_ids:
            sorted_lines = sorted(self.contact_line_ids, key=lambda line: line.sequence)
            if sorted_lines:
                self.name = self.contact_line_ids[0].name
                self.email = self.contact_line_ids[0].email
                self.phone = self.contact_line_ids[0].phone
                self.mobile = self.contact_line_ids[0].mobile
                self.function = self.contact_line_ids[0].funcion
            
    @api.onchange('ubicacion_line_ids')
    def _onchange_ubicacion_lines(self):
        print("onchange ubicacion lines")
        if self.ubicacion_line_ids:
            sorted_lines = sorted(self.ubicacion_line_ids, key=lambda line: line.sequence)
            if sorted_lines:
                self.type = self.ubicacion_line_ids[0].tipo
                self.contact_address = self.ubicacion_line_ids[0].contact_address
                self.ref = self.ubicacion_line_ids[0].ref
                self.city = self.ubicacion_line_ids[0].ciudad
                self.country_id = self.ubicacion_line_ids[0].pais_id