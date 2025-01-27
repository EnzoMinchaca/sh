from odoo import _, api, fields, models
from odoo.tools import float_round, html_escape
from odoo.exceptions import UserError
import num2words

class AccountMove(models.Model):
    _inherit = 'account.move'

    guia_remision = fields.Char(string='Guía de Remisión', compute='_compute_guia_remision', store=True)
    is_sale_edi_document = fields.Boolean(compute='_compute_guia_remision', store=True)
    orden_compra = fields.Char(string="Orden de Compra", store=True, copy=False)
    
    @api.depends('move_type', 'debit_origin_id')
    def _compute_guia_remision(self):
        for move in self:
            if move.move_type == 'out_invoice' and not move.debit_origin_id:
                guia_remision = []
                is_sale_order = False
                source_orders = move.line_ids.sale_line_ids.order_id
                if source_orders:
                    is_sale_order = True
                    for source_order in source_orders:
                        filtered_pickings = source_order.picking_ids.filtered(lambda p: p.l10n_latam_document_number)
                        guia_remision.extend(filtered_pickings.mapped('l10n_latam_document_number'))
                move.guia_remision = ', '.join(guia_remision)
                move.is_sale_edi_document = is_sale_order
            else:
                move.guia_remision = False
                move.is_sale_edi_document = False

    def _get_name_invoice_report(self):
        res = super()._get_name_invoice_report()
        if self.l10n_latam_use_documents and self.company_id.country_id.code == 'PE':
            # TODO: Se puede agregar un campo selection en el modelo de compañía
            # if self.company_id.l10n_pe_edi_template_layout == 'bold':
            #    res = 'dv_l10n_pe_edi_template_bold.report_pe_invoice_document'
            # if self.company_id.l10n_pe_edi_template_layout == 'light':
            #    res = 'dv_l10n_pe_edi_template_light.report_pe_invoice_document'
            res = 'dv_l10n_pe_edi_template_light.report_pe_invoice_document'
        return res

    def get_pe_tax_totals(self):
        ref = self.env.ref
        cid = self.env.company.id
        try:
            tax_group_igv = ref(f"account.{cid}_tax_group_igv").id
            tax_group_igv_g_ng = ref(f"account.{cid}_tax_group_igv_g_ng").id
            tax_group_igv_ng = ref(f"account.{cid}_tax_group_igv_ng").id
            tax_group_exp = ref(f"account.{cid}_tax_group_exp").id
            tax_group_exo = ref(f"account.{cid}_tax_group_exo").id
            tax_group_ina = ref(f"account.{cid}_tax_group_ina").id
            tax_group_ivap = ref(f"account.{cid}_tax_group_ivap").id
            tax_group_icbper = ref(f"account.{cid}_tax_group_icbper").id
            tax_group_isc = ref(f"account.{cid}_tax_group_isc").id
            tax_group_gra = ref(f"account.{cid}_tax_group_gra").id
            tax_group_other = ref(f"account.{cid}_tax_group_other").id
            tax_group_ret = ref(f"account.{cid}_tax_group_ret").id
        except ValueError:
            raise UserError(
                "Actualice el módulo l10n_pe para actualizar los datos requeridos.")
        if len(self) == 1:
            where_clause = f"account_move_line__move_id.id = {self.id}"
        else:
            where_clause = f"account_move_line__move_id.id in {tuple(self.ids)}"

        query = f"""
            SELECT
                account_move_line__move_id.id,
                account_move_line__move_id.name as move_name,
                account_move_line__move_id.ref as move_ref,
                rp.name as partner_name,
                rp.vat as partner_vat,
                rp.street as partner_street,
                lit.name->>'en_US' as partner_lit,
                lit.l10n_pe_vat_code as partner_lit_code,
                rp.country_id as partner_country_id,
                account_move_line__move_id.currency_id,
                rc.name as currency_name,
                account_move_line__move_id__l10n_latam_document_type_id.code as document_type,
                account_move_line__move_id.id as move_id,
                account_move_line__move_id.move_type,
                account_move_line__move_id.date,
                account_move_line__move_id.invoice_date,
                account_move_line__move_id.invoice_date_due,
                account_move_line__move_id.partner_id,
                account_move_line__move_id.journal_id,
                account_move_line__move_id.name,
                account_move_line__move_id.l10n_latam_document_type_id as l10n_latam_document_type_id,
                account_move_line__move_id.state,
                account_move_line__move_id.company_id,
                reversed_entry.name as reversed_entry_name,
                reversed_entry.invoice_date as reversed_entry_date,
                reversed_entry.l10n_latam_document_type_id as reversed_entry_document_type_id,
                ldt_reversed_entry.code as reversed_entry_document_type,
                debit_origin.name as debit_origin_name,
                debit_origin.invoice_date as debit_origin_date,
                debit_origin.l10n_latam_document_type_id as debit_origin_document_type_id,
                ldt_debit_origin.code as debit_origin_document_type,
                partner_company.vat  AS company_vat,
                company.name AS company_name,
                ABS(sum(CASE WHEN btg.id = {tax_group_igv}
                    THEN account_move_line.amount_currency ELSE 0 END)) as base_igv,
                ABS(sum(CASE WHEN ntg.id = {tax_group_igv}
                    THEN account_move_line.amount_currency ELSE 0 END)) as vat_igv,
                ABS(sum(CASE WHEN btg.id = {tax_group_igv_g_ng}
                    THEN account_move_line.amount_currency ELSE 0 END)) as base_igv_g_ng,
                ABS(sum(CASE WHEN ntg.id = {tax_group_igv_g_ng}
                    THEN account_move_line.amount_currency ELSE 0 END)) as vat_igv_g_ng,
                ABS(sum(CASE WHEN btg.id = {tax_group_igv_ng}
                    THEN account_move_line.amount_currency ELSE 0 END)) as base_igv_ng,
                ABS(sum(CASE WHEN ntg.id = {tax_group_igv_ng}
                    THEN account_move_line.amount_currency ELSE 0 END)) as vat_igv_ng,
                ABS(sum(CASE WHEN btg.id = {tax_group_exp}
                    THEN account_move_line.amount_currency ELSE 0 END)) as base_exp,
                ABS(sum(CASE WHEN ntg.id = {tax_group_exp}
                    THEN account_move_line.amount_currency ELSE 0 END)) as vat_exp,
                ABS(sum(CASE WHEN btg.id = {tax_group_exo}
                    THEN account_move_line.amount_currency ELSE 0 END)) as base_exo,
                ABS(sum(CASE WHEN ntg.id = {tax_group_exo}
                    THEN account_move_line.amount_currency ELSE 0 END)) as vat_exo,
                ABS(sum(CASE WHEN btg.id = {tax_group_ina}
                    THEN account_move_line.amount_currency ELSE 0 END)) as base_ina,
                ABS(sum(CASE WHEN ntg.id = {tax_group_ina}
                    THEN account_move_line.amount_currency ELSE 0 END)) as vat_ina,
                ABS(sum(CASE WHEN btg.id = {tax_group_ivap}
                    THEN account_move_line.amount_currency ELSE 0 END)) as base_ivap,
                ABS(sum(CASE WHEN ntg.id = {tax_group_ivap}
                    THEN account_move_line.amount_currency ELSE 0 END)) as vat_ivap,
                ABS(sum(CASE WHEN btg.id = {tax_group_icbper}
                    THEN account_move_line.amount_currency ELSE 0 END)) as base_icbper,
                ABS(sum(CASE WHEN ntg.id = {tax_group_icbper}
                    THEN account_move_line.amount_currency ELSE 0 END)) as vat_icbper,
                ABS(sum(CASE WHEN btg.id = {tax_group_isc}
                    THEN account_move_line.amount_currency ELSE 0 END)) as base_isc,
                ABS(sum(CASE WHEN ntg.id = {tax_group_isc}
                    THEN account_move_line.amount_currency ELSE 0 END)) as vat_isc,
                ABS(sum(CASE WHEN btg.id = {tax_group_gra}
                    THEN account_move_line.amount_currency ELSE 0 END)) as base_free,
                ABS(sum(CASE WHEN ntg.id = {tax_group_gra}
                    THEN account_move_line.amount_currency ELSE 0 END)) as vat_free,
                ABS(sum(CASE WHEN btg.id = {tax_group_other}
                    THEN account_move_line.amount_currency ELSE 0 END)) as base_other,
                ABS(sum(CASE WHEN ntg.id = {tax_group_other}
                    THEN account_move_line.amount_currency ELSE 0 END)) as vat_other,
                ABS(sum(CASE WHEN btg.id = {tax_group_ret}
                    THEN account_move_line.amount_currency ELSE 0 END)) as base_withholding,
                ABS(sum(CASE WHEN ntg.id = {tax_group_ret}
                    THEN account_move_line.amount_currency ELSE 0 END)) as vat_withholding,
                ABS(account_move_line__move_id.amount_total) as total,
                ABS(account_move_line__move_id.amount_total_signed) as amount_currency
            FROM
                account_move_line
            LEFT JOIN
                account_move as account_move_line__move_id
                ON account_move_line.move_id = account_move_line__move_id.id
            LEFT JOIN
                -- nt = net tax
                account_tax AS nt
                ON account_move_line.tax_line_id = nt.id
            LEFT JOIN
                account_move_line_account_tax_rel AS account_move_linetr
                ON account_move_line.id = account_move_linetr.account_move_line_id
            LEFT JOIN
                -- bt = base tax
                account_tax AS bt
                ON account_move_linetr.account_tax_id = bt.id
            LEFT JOIN
                account_tax_group AS btg
                ON btg.id = bt.tax_group_id
            LEFT JOIN
                account_tax_group AS ntg
                ON ntg.id = nt.tax_group_id
            LEFT JOIN
                res_partner AS rp
                ON rp.id = account_move_line__move_id.commercial_partner_id
            LEFT JOIN
                res_country AS rpc
                ON rpc.id = rp.country_id
            LEFT JOIN
                l10n_latam_identification_type AS lit
                ON rp.l10n_latam_identification_type_id = lit.id
            LEFT JOIN
                res_currency AS rc
                ON rc.id = account_move_line__move_id.currency_id
            LEFT JOIN
                l10n_latam_document_type AS account_move_line__move_id__l10n_latam_document_type_id
                ON account_move_line__move_id__l10n_latam_document_type_id.id = account_move_line__move_id.l10n_latam_document_type_id
            LEFT JOIN
                account_move AS reversed_entry
                ON reversed_entry.id = account_move_line__move_id.reversed_entry_id
            LEFT JOIN
                l10n_latam_document_type AS ldt_reversed_entry
                ON ldt_reversed_entry.id = reversed_entry.l10n_latam_document_type_id
            LEFT JOIN
                account_move AS debit_origin
                ON debit_origin.id = account_move_line__move_id.debit_origin_id
            LEFT JOIN
                l10n_latam_document_type AS ldt_debit_origin
                ON ldt_debit_origin.id = debit_origin.l10n_latam_document_type_id
            LEFT JOIN
                account_journal AS aj
                ON aj.id = account_move_line__move_id.journal_id
            LEFT JOIN
                res_company AS company
                ON company.id = account_move_line__move_id.company_id
            LEFT JOIN
                res_partner AS partner_company
                ON partner_company.id = company.partner_id
            WHERE
                {where_clause}
                AND (account_move_line.tax_line_id is not null or btg.l10n_pe_edi_code is not null)
                AND aj.l10n_latam_use_documents
            GROUP BY
                account_move_line__move_id.id, rp.id, lit.id, rc.id, account_move_line__move_id__l10n_latam_document_type_id.id,
                reversed_entry.id, ldt_reversed_entry.id, debit_origin.id,
                ldt_debit_origin.id, rpc.id, company.id, partner_company.id
            ORDER BY
                account_move_line__move_id.date, account_move_line__move_id.name
        """

        self.env.cr.execute(query)
        query_res_lines = self.env.cr.dictfetchall()

        return query_res_lines
    
    # Importe en moneda con formato nacional PE:
    amount_total_text = fields.Char(
        string='Monto total en letras',
        compute='_compute_amount_text',
    )
    
    CURRENCY_TRANSLATIONS = {
        'USD': 'Dólares',
        'PEN': 'Soles',
        'EUR': 'Euros',
    }
    @api.depends('amount_total', 'currency_id')
    def _compute_amount_text(self):
        for record in self:
            if record.amount_total and record.currency_id:
                # Convertir amount_total a palabras
                amount_total_numero = int(record.amount_total)  # Obtener la parte entera del amount_total
                amount_total_decimal = round((record.amount_total - amount_total_numero) * 100)  # Obtener la parte decimal
                amount_total_texto = num2words.num2words(amount_total_numero, lang='es').capitalize()  # Convertir parte entera a palabras
                if amount_total_decimal > 0:
                    amount_total_texto += f' con {amount_total_decimal:02d}/100'  # Agregar parte decimal si existe
                currency_name_translated = self.CURRENCY_TRANSLATIONS.get(record.currency_id.name, record.currency_id.currency_unit_label)
                amount_total_texto += f' {currency_name_translated}'  # Agregar nombre de la moneda
                record.amount_total_text = amount_total_texto.upper()
            else:
                record.amount_total_text = ''
