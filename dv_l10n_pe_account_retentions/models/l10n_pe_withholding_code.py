from odoo import api, fields, models


class WithholdingCode(models.Model):
    _name = 'l10n_pe.withholding.code'
    _description = 'Tabla de Retenciones'

    name = fields.Char(string='Nombre')
    code = fields.Char(string='Código')
    percentage = fields.Float(string='Porcentaje')

    @api.constrains('percentage')
    def _check_percentage(self):
        for record in self:
            if record.percentage == 0:
                raise models.ValidationError(
                    'El porcentaje no puede ser 0')

    def name_get(self):
        res = []
        for record in self:
            complete_name = f"{record.code}: {record.name}"
            res.append((record.id, complete_name))
        return res
