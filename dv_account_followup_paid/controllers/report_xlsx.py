try:
   from odoo.tools.misc import xlsxwriter
except ImportError:
   import xlsxwriter

from odoo import http
from odoo.http import request
import io
import base64

import logging

_logger = logging.getLogger(__name__)


class ReportPaidXlsxController(http.Controller):

    @http.route('/move_line/export_xlsx', type='http', auth='user')
    def get_move_line_paid_report(self, ids=None, group_by=None, **kwargs):

        # Convertir los IDs de la URL en una lista de enteros
        ids_list = [int(x) for x in ids.split(',') if x.isdigit()]

        # Procesar group_by si es necesario
        group_by_list = group_by.split(',') if group_by else []
        group_name = group_by_list[0] if group_by_list else False
    
        move_lines = request.env['account.followup.paid'].browse(ids_list)
        
        # Crear un buffer en memoria para guardar el archivo XLSX
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Reporte')

        worksheet.set_column('A:A', 15)  # Ancho para la columna 'Fecha Emisión'
        worksheet.set_column('B:B', 20)  # Ancho para la columna 'N° Documento'
        worksheet.set_column('C:C', 18)  # Ancho para la columna 'Cliente'
        worksheet.set_column('D:D', 15)  # Ancho para la columna 'Fecha de Pago'
        worksheet.set_column('E:E', 15)  # Ancho para la columna 'Vendedor'
        worksheet.set_column('F:F', 15)  # Ancho para la columna 'Importe en $'
        worksheet.set_column('G:G', 15)  # Ancho para la columna 'Importe en S/'

        title_format = workbook.add_format({'bold': True, 'font_size': 14, 'bg_color': '#D3D3D3', 'align': 'center'})
        label_format = workbook.add_format({'bold': True})

        company = request.env.company

        worksheet.merge_range('A1:G1', 'Reporte de Cobranza Efectiva', title_format)
        worksheet.write('A2', company.name or '', label_format)
        worksheet.write('A3', company.country_id.name or '', label_format)
        worksheet.write('A4', company.vat or '', label_format)

        headers = ['Fecha Emisión', 'N° Documento', 'Cliente', 'Fecha de Pago', 'Vendedor', 'Monto en $', 'Monto en S/']
        header_format = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#D3D3D3'})

        start_row = 6

        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})

        grouped_data = {}

        if group_name:
            for line in move_lines:
                # Obtener el valor del campo de agrupación dinámicamente
                group_value = getattr(line, group_name, None)
                
                # Si el campo es un registro de Odoo (relacional), tomamos el nombre
                group_key = group_value.name if hasattr(group_value, 'name') else group_value or 'Sin Agrupación'

                if group_key not in grouped_data:
                    grouped_data[group_key] = []

                grouped_data[group_key].append(line)
        else:
            # Si no hay agrupación, simplemente añadimos todas las líneas sin agrupar
            grouped_data['Sin Agrupación'] = move_lines

        total_usd_general = 0.0
        total_pen_general = 0.0
        
        row = start_row
        for group_key, lines in grouped_data.items():
            worksheet.write(row, 0, group_key, header_format)
            row += 1

            for col, header in enumerate(headers):
                worksheet.write(row, col, header, header_format)
            
            row += 1

            for line in lines:
                worksheet.write_datetime(row, 0, line.date if line.date else '', date_format)
                worksheet.write(row, 1, line.document_number or '')
                worksheet.write(row, 2, line.partner_id.name or '')
                worksheet.write_datetime(row, 3, line.account_payment_date if line.account_payment_date else '', date_format)
                worksheet.write(row, 4, line.seller_account.name or '')
                worksheet.write(row, 5, line.amount_no_sign_usd or 0.0)
                worksheet.write(row, 6, line.amount_no_sign_pen or 0.0)
                row += 1

                # Acumula los totales generales
                total_usd_general += line.amount_no_sign_usd or 0.0
                total_pen_general += line.amount_no_sign_pen or 0.0

            total_usd = sum(line.amount_no_sign_usd for line in lines)
            total_pen = sum(line.amount_no_sign_pen for line in lines)

            worksheet.write(row, 4, 'Total en $', header_format)
            worksheet.write(row, 5, total_usd, header_format)
            row += 1
            worksheet.write(row, 4, 'Total en S/', header_format)
            worksheet.write(row, 6, total_pen, header_format)
            row += 5

        # Escribe los totales generales al final del reporte
        worksheet.write(row, 4, 'Totales Generales', header_format)
        worksheet.write(row, 5, f"$ {round(total_usd_general, 2)}", header_format)
        worksheet.write(row, 6, f"S/ {round(total_pen_general, 2)}", header_format)

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
                ('Content-Disposition', f'attachment; filename="reporte_cobranza_efectiva.xlsx"')
            ]
        )