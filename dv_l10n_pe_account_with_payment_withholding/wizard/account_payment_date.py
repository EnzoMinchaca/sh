from odoo import models, api, fields
from odoo.exceptions import UserError

class AccountPaymentDate(models.TransientModel):
    _name = 'account.payment.date'

    _description = 'Wizard to capture payment date'
 
    # Esto ya tiene los valores predefinidos
    l10n_pe_withholding_subject_invoice_ids = fields.Many2many(
        # model - name_entity - 1° atribute - 2° atribute
        'account.move', 'account_payment_register_preview_date', 'account_payment_register_id', 'account_move_id',
        string='Facturas sujetas a retención', store=True
    )

    payment_date_retention = fields.Date(string='Fecha de Pago')

    @api.model
    def create(self, vals):
        res = super(AccountPaymentDate, self).create(vals)

        # Validación de facturas
        for invoice in res.l10n_pe_withholding_subject_invoice_ids:
            if invoice.amount_retention <= 0:
                raise UserError(f"No puede registrar un pago de retención porque no queda nada por pagar en la factura {invoice.name}.")

        return res

    def set_payment_type_and_register_payment(self):

        var = self.env['retention.payment.wizard.ultimate'].create({
            'l10n_pe_withholding_subject_invoice_ids': self.l10n_pe_withholding_subject_invoice_ids,
            'payment_date': self.payment_date_retention
        })
        
        return {
            'name': 'Registrar pago de retenciones',
            'type': 'ir.actions.act_window',
            'res_model': 'retention.payment.wizard.ultimate',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': var.id,
            'target': 'new',
        }

