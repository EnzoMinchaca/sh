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