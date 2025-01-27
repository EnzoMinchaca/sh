from odoo import models, fields, api
from odoo.exceptions import UserError
import base64

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    applicant_company = fields.Char(string="Empresa Solicitante", store=True)
    date_event = fields.Date(string='Fecha Evento', store=True)
    time_start = fields.Char(string="Hora Evento Comienzo", help="Formato HH:MM", store=True)
    time_finish = fields.Char(string="Hora Evento Fin", help="Formato HH:MM", store=True)
    celebration = fields.Char(string="Tipo Celebración", store=True)
    duration = fields.Char(string="Duración", store=True)
    zone_launch = fields.Char(string="Zona lanzamiento", store=True)
    ubication_event = fields.Char(string="Ubicación", store=True)
    technical = fields.Many2one("res.partner", string="Técnico Asignado", store=True)
    vehicle = fields.Char(string="Vehículo Placa", store=True)
    note_custom = fields.Text(string="Nota Adicional", store=True)
    #description_general = fields.Text(string="Descripción General", store=True)
    description_bomberos = fields.Text(string="Descripción Permiso Bomberos", store=True)
    description_interior = fields.Text(string="Descripción Permiso Interior", store=True)
    description_ambiente = fields.Text(string="Descripción Permiso Ambiente", store=True)

    @api.model
    def _create_pdf_attachment(self, sale_order):
        # Me traigo la compañia
        # company = self.env['res.company'].search([('name', '=', 'Wizard Group Srl')], limit=1)
        # if company:
        #     descriptions = [
        #         ('Bomberos', self.description_bomberos, 'Solicitud Permiso Espectáculo Fuegos Artificiales Cuerpo Bomberos'),
        #         ('Interior', self.description_interior, 'Solicitud Permiso Espectáculo Fuegos Artificiales ministerio de Interior y Policía'),
        #         ('Ambiente', self.description_ambiente, 'Solicitud Permiso Espectáculo Fuegos Artificiales ministerio de Medio Ambiente')
        #     ]
        # else:
        #     descriptions = [
        #         ('Bomberos', self.description_bomberos, 'Solicitud Permiso Espectáculo Fuegos Artificiales Cuerpo Bomberos'),
        #         ('Interior', self.description_interior, 'Solicitud Permiso Espectáculo Fuegos Artificiales ministerio de Interior y Policía'),
        #         ('Ambiente', self.description_ambiente, 'Solicitud Permiso Espectáculo Fuegos Artificiales ministerio de Medio Ambiente')
        #     ]
        descriptions = [
                ('Bomberos', self.description_bomberos, 'Solicitud Permiso Espectáculo Fuegos Artificiales Cuerpo Bomberos'),
                ('Interior', self.description_interior, 'Solicitud Permiso Espectáculo Fuegos Artificiales ministerio de Interior y Policía'),
                ('Ambiente', self.description_ambiente, 'Solicitud Permiso Espectáculo Fuegos Artificiales ministerio de Medio Ambiente')
            ]
        # Crear el los 3 pdf
        for field_name, description, text in descriptions:
            # Verificar si ya existe un adjunto con el nombre específico para cada campo
            existing_attachment = self.env['ir.attachment'].search([
                ('res_model', '=', 'sale.order'),
                ('res_id', '=', sale_order.id),
                ('name', '=', f'{sale_order.name} - {field_name}.pdf')
            ], limit=1)

            # Si el archivo ya existe, saltarse la creación
            if existing_attachment:
                continue
            # Renderizar el PDF con el campo correspondiente
            pdf_content = self._generate_pdf_for_description(sale_order, description, field_name, text)
            # Crear el archivo adjunto
            self.env['ir.attachment'].create({
                'name': f'{sale_order.name} - {field_name}.pdf',
                'type': 'binary',
                'datas': base64.b64encode(pdf_content).decode('utf-8'),
                'res_model': 'sale.order',
                'res_id': sale_order.id,
                'mimetype': 'application/pdf',
            })
        return True
    
    def _generate_pdf_for_description(self, sale_order, description, field_name, text):
        report = self.env['ir.actions.report'].sudo().search([('name', '=', 'Formato de Permiso')], limit=1)
        if not report:
            raise UserError("No se encontró un reporte válido para 'dv_sales_document.report_sale_order_template'.")

        try:
            pdf_content, _ = self.env['ir.actions.report'].sudo()._render_qweb_pdf('dv_sales_document.report_sale_order_template', [sale_order.id], data={'description_field': description, 'field_name': field_name, 'text': text})
        except Exception as e:
            raise UserError(f"Error al renderizar el PDF: {str(e)}")
        
        if not pdf_content:
            raise UserError("El contenido del PDF no se generó correctamente.")
        
        return pdf_content

    def write(self, vals):
        result = super(SaleOrder, self).write(vals)
        
        for order in self:
            if order.state == 'sale':
                # Llamar a la función para crear y adjuntar el PDF
                self._create_pdf_attachment(order)
        return result
