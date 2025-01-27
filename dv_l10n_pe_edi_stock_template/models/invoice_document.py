from odoo import models, fields, api, _

class InvoiceDocument(models.Model):
    _inherit = 'stock.picking'

    invoice_document_type_id = fields.Many2one('l10n_latam.document.type', string='Tipo de documento del comprobante', compute='_compute_invoice_data')
    invoice_document_number = fields.Char(string='Numero del comprobante', compute='_compute_invoice_data')
    
    @api.depends('origin')
    def _compute_invoice_data(self):
        for picking in self:
            if picking.origin:
                sale_order = self.env['sale.order'].search([('name', '=', picking.origin)], limit=1)
                if sale_order:
                    invoice = sale_order.invoice_ids and sale_order.invoice_ids[0]
                    picking.invoice_document_type_id = invoice.l10n_latam_document_type_id
                    picking.invoice_document_number = invoice.l10n_latam_document_number
                else:
                    picking.invoice_document_type_id = False
                    picking.invoice_document_number = "No se encontro la factura asociada."
            else:
                picking.invoice_document_type_id = False
                picking.invoice_document_number = "No se encontro la factura asociada."