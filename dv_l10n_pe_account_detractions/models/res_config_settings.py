from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    l10n_pe_spot_mode = fields.Selection(
        [('off', 'Desactivado'), ('same_move', 'Mismo asiento de la factura'),
         ('new_move', 'Asiento separado')],
        related='company_id.l10n_pe_spot_mode', string="Modo registro de detracción", readonly=False,
        help="Dependiendo del modo, la detracción se registrará en el mismo asiento de la factura o en un asiento separado que se conciliará con la factura.")

    l10n_pe_spot_journal_id = fields.Many2one(
        'account.journal', related='company_id.l10n_pe_spot_journal_id', string="Diario de detracciones",
        domain=lambda self: [('type', '=', 'general')], readonly=False,
        help="Diario que será utilizado para registrar las detracciones.")

    l10n_pe_spot_payable_account_id = fields.Many2one(
        'account.account', related='company_id.l10n_pe_spot_payable_account_id', string="Cuenta de detracciones por pagar",
        domain=lambda self: [('deprecated', '=', False)], readonly=False,
        help="Cuenta que será utilizada para registrar las detracciones por pagar.")

    l10n_pe_spot_receivable_account_id = fields.Many2one(
        'account.account', related='company_id.l10n_pe_spot_receivable_account_id', string="Cuenta de detracciones por cobrar",
        domain=lambda self: [('deprecated', '=', False)], readonly=False,
        help="Cuenta que será utilizada para registrar las detracciones por cobrar.")
