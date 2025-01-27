from odoo import models, fields, api
import qrcode
import base64
from io import BytesIO


class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_url = fields.Char(string="Invoice URL")
    qr_code_image = fields.Binary(string="QR Code Image", compute="_compute_qr_code_image", store=False)
    show_qr_code = fields.Boolean(string="Print QR Code", default=False)

    def _update_invoice_url(self):
        config = self.env['res.config.settings'].sudo().get_values()
        if self.state == 'posted':
            if config['downloadable']:
                self.invoice_url = self.get_base_url() + self._get_share_url(redirect=True)
            elif config['custom']:
                if not self.invoice_url:
                    self.invoice_url = ""  
            elif config['static']:
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                self.invoice_url = f"{base_url}/report/pdf/account.report_invoice/{self.id}"
            else:
                self.invoice_url = ''
        else:
            self.invoice_url = ''

    def action_post(self):
        res = super(AccountMove, self).action_post()
        self._update_invoice_url()
        return res

    @api.depends('invoice_url', 'show_qr_code')
    def _compute_qr_code_image(self):
        for record in self:
            if record.invoice_url and record.show_qr_code:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(record.invoice_url)
                qr.make(fit=True)
                img = qr.make_image(fill='black', back_color='white')
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                record.qr_code_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
            else:
                record.qr_code_image = False

    @api.onchange('show_qr_code')
    def _onchange_show_qr_code(self):
        if self.show_qr_code and self.state == 'posted':
            self._compute_qr_code_image()
