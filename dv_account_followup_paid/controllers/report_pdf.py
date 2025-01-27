from odoo import http
from odoo.http import request
import json

import logging

_logger = logging.getLogger(__name__)

class AccountPaidReportController(http.Controller):

    @http.route('/account_paid/report', type='http', auth='user')
    def generate_paid_report(self, ids=None, group_by=None, **kwargs):

        if not ids:
            return request.not_found()

        # Procesar group_by si es necesario
        group_by_list = group_by.split(',') if group_by else []

        ids_list = [int(x) for x in ids.split(',') if x.isdigit()]

        # Obtener los registros de las líneas de movimiento
        records = request.env['account.followup.paid'].search_read([('id', 'in', ids_list)], 
                                                               ['date', 'document_number', 'partner_id', 
                                                                'account_payment_date', 'seller_account', 
                                                                'amount_no_sign_usd', 'amount_no_sign_pen'])

        grouped_records = {}

        if group_by_list:
            group_name = group_by_list[0]

            if group_name == 'partner_id':
                group = 'Cliente: '
            elif group_name == 'seller_account':
                group = 'Vendedor: '

            for record in records:
                key_name = record[group_name] and record[group_name][1] or 'Sin Nombre'  # Usar el nombre del cliente o vendedor
                key = f"{group}{key_name}"
                if key not in grouped_records:
                    grouped_records[key] = []
                grouped_records[key].append(record)

        else:
            # Si no se especifica agrupación, usar todos los registros juntos
            grouped_records['Todos'] = records

        # Preparar los datos para el informe
        docs = [{'key': key, 'lines': lines} for key, lines in grouped_records.items()]

        pdf, _ = request.env['ir.actions.report']._render_qweb_pdf('dv_account_followup_paid.action_report_account_pdf', ids_list, data={'docs_': docs})
        
        # Devolver el PDF como una respuesta HTTP
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
        return request.make_response(pdf, headers=pdfhttpheaders)
