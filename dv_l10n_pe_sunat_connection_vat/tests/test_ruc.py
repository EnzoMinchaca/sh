from odoo.tests.common import TransactionCase


class TestRucConnection(TransactionCase):

    # Caso de uso #2: Obteniendo datos de un RUC
    def test_update_ruc_data(self):
        res = self.env['res.partner'].create({
            'name': 'Temporal',
            'vat': '20609861097',
            'l10n_latam_identification_type_id': self.env.ref('l10n_pe.it_RUC').id,
        })
        self.env['ir.config_parameter'].sudo().set_param('sunat.annexed_locals', True)
        self.env['ir.config_parameter'].sudo().set_param('sunat.get_annexed_locals', True)
        
        res.action_sunnat_connection_vat()
        self.assertEqual(res.name, 'DEVELOGERS E.I.R.L.')
