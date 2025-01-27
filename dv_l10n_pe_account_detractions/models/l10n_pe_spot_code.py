from odoo import api, fields, models


class L10nPeSpotCode(models.Model):
    _name = 'l10n_pe.spot.code'
    _description = 'Tabla de detracciones'
    _sql_constraints = [('code_unique', 'unique(code)',
                         'El código debe ser único')]

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código', required=True)

    percentage = fields.Float(string='Porcentaje')

    def name_get(self):
        res = []
        for record in self:
            complete_name = f"{record.code}: {record.name}"
            res.append((record.id, complete_name))
        return res

    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', operator, name), ('name', operator, name)]
        records = self.search(domain + args, limit=limit)
        return records.name_get()
