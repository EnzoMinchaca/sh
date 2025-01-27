# TODO integrar con modulo de pagos que reacomodan las cuentas contables por pagar y por cobrar

from odoo import _, api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_post(self):
        super(AccountPayment, self).action_post()
        for payment in self:
            payment._generate_line_ids()

    def _generate_line_ids(self):
        """
        Reacomoda las lineas del asiento contable del pago para que sea una linea por cada factura
        """
        pass
        # self.ensure_one()
        # self = self.with_context(skip_account_move_synchronization=True)

        # new_payment_lines = []
        # # Agregar la linea bancaria
        # for line in self.line_ids.filtered(lambda l: l.account_id.account_type not in ['asset_receivable', 'liability_payable']):
        #     if self.payment_type == 'inbound':
        #         amount = self.amount
        #     else:
        #         amount = self.amount*(-1)
        #     new_payment_lines.append((0, 0, {
        #         'name': line.name,
        #         'account_id': line.account_id.id,
        #         'currency_id': line.currency_id.id,
        #         'amount_currency': amount,
        #         'date_maturity': line.date_maturity,
        #     }))
        # # Agregar las lineas de comprobantes
        # for line in self.payment_move_line_ids.filtered(lambda l: l.account_id.account_type in ['asset_receivable', 'liability_payable'] and l.amount_to_pay > 0):
        #     if line.account_id.account_type == 'asset_receivable':
        #         amount_to_pay = line.amount_to_pay*(-1)
        #     else:
        #         amount_to_pay = line.amount_to_pay
        #     new_payment_lines.append((0, 0, {
        #         'name': line.move_name,
        #         'account_id': line.account_id.id,
        #         'currency_id': line.currency_id.id,
        #         'amount_currency': amount_to_pay,
        #         'date_maturity': line.date_maturity,
        #     }))

        # self.write({'line_ids': [(5, 0, 0)]})
        # self.write({'line_ids': new_payment_lines})
