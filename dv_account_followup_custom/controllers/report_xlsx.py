try:
   from odoo.tools.misc import xlsxwriter
except ImportError:
   import xlsxwriter

from odoo import http
from odoo.http import request
import io
import base64


class ReportXlsxController(http.Controller):

    @http.route('/partner/move_line/<int:partner_id>', type='http', auth='user')
    def get_move_line_report(self, partner_id, **kwargs):
        partner = request.env['res.partner'].browse(partner_id)
        if not partner:
            return request.not_found()
        
        # Crear un buffer en memoria para guardar el archivo XLSX
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Reporte de Seguimiento')

        worksheet.set_column('A:A', 15)  # Ancho para la columna 'Fecha Emisión'
        worksheet.set_column('B:B', 20)  # Ancho para la columna 'N° Documento'
        worksheet.set_column('C:C', 18)  # Ancho para la columna 'Fecha Vencimiento'
        worksheet.set_column('D:D', 15)  # Ancho para la columna 'Importe en $'
        worksheet.set_column('E:E', 15)  # Ancho para la columna 'Importe en S/'

        title_format = workbook.add_format({'bold': True, 'font_size': 14, 'bg_color': '#D3D3D3', 'align': 'center'})
        label_format = workbook.add_format({'bold': True})

        worksheet.merge_range('A1:E1', 'Reporte de Seguimiento', title_format)
        worksheet.write('A2', partner.env.company.name or '', label_format)
        worksheet.write('A3', partner.env.company.country_id.name or '', label_format)
        worksheet.write('A4', partner.env.company.vat or '', label_format)
        worksheet.write('A5', f"Cliente: {partner.name}" or '', label_format)

        headers = ['Fecha Emisión', 'N° Documento', 'Fecha Vencimiento', 'Importe en $', 'Importe en S/']
        header_format = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#D3D3D3'})

        start_row = 7

        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})

        for col, header in enumerate(headers):
            worksheet.write(start_row, col, header, header_format)

        # Ordenar las líneas por la fecha de emisión (new_date) de manera descendente
        sorted_lines = partner.unreconciled_aml_ids.sorted(key=lambda l: l.new_date, reverse=True)

        row = start_row + 1
        for line in sorted_lines:
            worksheet.write_datetime(row, 0, line.new_date if line.new_date else '', date_format)
            worksheet.write(row, 1, line.new_move_name or '')
            worksheet.write_datetime(row, 2, line.date_maturity if line.date_maturity else '', date_format)
            worksheet.write(row, 3, line.amount_usd or 0.0)
            worksheet.write(row, 4, line.amount_pen or 0.0)
            row += 1

        total_usd = sum(line.amount_usd for line in sorted_lines)
        total_pen = sum(line.amount_pen for line in sorted_lines)

        worksheet.write(row, 2, 'Total en $', header_format)
        worksheet.write(row, 3, total_usd, header_format)
        worksheet.write(row + 1, 2, 'Total en S/', header_format)
        worksheet.write(row + 1, 4, total_pen, header_format)

        # Cerrar el workbook
        workbook.close()
        output.seek(0)
        
        # Preparar la respuesta del archivo XLSX
        xlsx_data = output.read()
        output.close()
        return request.make_response(
            xlsx_data,
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', f'attachment; filename="reporte_seguimiento_{partner.name}.xlsx"')
            ]
        )