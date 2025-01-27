from odoo import http
from odoo.http import request
from odoo.exceptions import UserError
import base64

class ReportDownloadController(http.Controller):

    @http.route('/reporte_facturas/download/<int:attachment_id>', type='http', auth='user')
    def download_report(self, attachment_id, **kwargs):
        #busco el pdf que cree con su id
        attachment = request.env['ir.attachment'].sudo().browse(attachment_id)

        if not attachment.exists():
            raise UserError("El archivo no existe.")

        #preparo el pdf
        file_content = base64.b64decode(attachment.datas)
        file_name = attachment.name

        #lo muestro en el navegador
        return request.make_response(file_content, headers=[
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', f'inline; filename="{file_name}"')
        ])

