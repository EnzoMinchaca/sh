from odoo.tests.common import TransactionCase


class TestDniConnection(TransactionCase):

    # Caso de uso #1: Obteniendo datos de un DNI
    def test_update_dni_data(self):
        res = self.env['res.partner'].create({
            'name': 'Temporal',
            'vat': '75539032',
            'l10n_latam_identification_type_id': self.env.ref('l10n_pe.it_DNI').id,
        })
        res.action_sunnat_connection_vat()
        self.assertEqual(res.name, 'SALGUERO BAZALAR AILTON JESUS')
