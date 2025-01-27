from odoo import api, fields, models, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    orden_compra = fields.Char(string="Orden de Compra", store=True)

    def get_transport_type_label(self):
        self.ensure_one()
        # Diccionario de traducciones manuales
        translations = {
            '01': 'Transporte Público',
            '02': 'Transporte Privado'
        }
        # Obtener la traducción correspondiente al valor seleccionado
        return translations.get(self.l10n_pe_edi_transport_type, '')
    
    def get_reason_for_transfer_label(self):
        self.ensure_one()
        # Diccionario de traducciones manuales
        translations = {
            '01': 'Venta',
            '03': 'Venta con entrega a terceros',
            '04': 'Transferencia entre establecimientos de la misma empresa',
            '05': 'Envíos',
            '13': 'Otros',
            '14': 'Venta sujeta a confirmación del comprador',
            '17': 'Transferencia de bienes para transformación',
            '18': 'Emisor ambulante traslado CP',
        }
        # Obtener la traducción correspondiente al valor seleccionado
        return translations.get(self.l10n_pe_edi_reason_for_transfer, '')