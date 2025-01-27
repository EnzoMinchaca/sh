from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    get_data_from_dni = fields.Boolean(
        'Obtener datos desde DNI', config_parameter='sunat.get_data_from_dni')
    get_data_from_ruc = fields.Boolean(
        'Obtener datos desde RUC', config_parameter='sunat.get_data_from_ruc')
    
    get_annexed_locals = fields.Boolean(
        'Agregar locales anexos', config_parameter='sunat.get_annexed_locals')
    get_legal_representatives = fields.Boolean(
        'Agregar representantes legales', config_parameter='sunat.get_legal_representatives')

    @api.onchange('get_data_from_ruc')
    def _onchange_get_data_from_ruc(self):
        if not self.get_data_from_ruc:
            self.get_annexed_locals = False
            self.get_legal_representatives = False