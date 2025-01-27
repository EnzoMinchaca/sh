# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, get_lang

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    account_analytic_id = fields.Many2one('account.analytic.account', 'SKU')
    account_id = fields.Many2one('account.account', 'Cuenta contable')

    def _prepare_account_move_line(self, move=False):
        # Llamar al método original para obtener el resultado original
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move=move)

        # Añadir los nuevos campos al diccionario `res`
        res.update({
            'account_id': self.account_id.id,
        })

        return res