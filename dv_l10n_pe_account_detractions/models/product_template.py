from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    l10n_pe_withhold_code = fields.Selection(
        selection=[
            ('001', 'Azúcar y melaza de caña'),
            ('002', 'Arroz'),
            ('003', 'Alcohol etílico'),
            ('004', 'Recursos hidrobiológicos'),
            ('005', 'Maíz amarillo duro'),
            ('006', 'Algodón (Obsoleto)'),
            ('007', 'Caña de azúcar'),
            ('008', 'Madera'),
            ('009', 'Arena y piedra'),
            ('010', 'Residuos, subproductos, desechos, recortes y desperdicios'),
            ('011', 'Bienes gravados con el IGV, o renuncia a la exoneración'),
            ('012', 'Intermediación laboral y tercerización'),
            ('013', 'Animales vivos'),
            ('014', 'Carnes y despojos comestibles'),
            ('015', 'Abonos, cueros y pieles de origen animal'),
            ('016', 'Aceite de pescado'),
            ('017', 'Harina, polvo y “pellets” de pescado, crustáceos, moluscos y demás invertebrados acuáticos'),
            ('018', 'Embarcaciones pesqueras (Obsoleto)'),
            ('019', 'Arrendamiento de bienes muebles'),
            ('020', 'Mantenimiento y reparación de bienes muebles'),
            ('021', 'Movimiento de carga'),
            ('022', 'Otros servicios empresariales'),
            ('023', 'Leche'),
            ('024', 'Comisión mercantil'),
            ('025', 'Fabricación de bienes por encargo'),
            ('026', 'Servicio de transporte de personas'),
            ('027', 'Servicio de transporte de carga'),
            ('028', 'Transporte de pasajeros'),
            ('029', 'Algodón en rama sin desmontar (Obsoleto)'),
            ('030', 'Contratos de construcción'),
            ('031', 'Oro gravado con el IGV'),
            ('032', 'Páprika y otros frutos de los géneros capsicum o pimienta'),
            ('033', 'Espárragos (Obsoleto)'),
            ('034', 'Minerales metálicos no auríferos'),
            ('035', 'Bienes exonerados del IGV'),
            ('036', 'Oro y demás minerales metálicos exonerados del IGV'),
            ('037', 'Demás servicios gravados con el IGV'),
            ('039', 'Minerales no metálicos'),
            ('040', 'Bien inmueble gravado con IGV'),
            ('041', 'Plomo'),
            ('099', 'Ley 30737'),
        ],
        string="Código de detracción",)
    l10n_pe_withhold_percentage = fields.Float(
        string="Porcentaje de detracción")

    @api.onchange('l10n_pe_withhold_code')
    def _onchange_l10n_pe_withhold_code(self):
        if self.l10n_pe_withhold_code:
            self.l10n_pe_withhold_percentage = self.env['l10n_pe.spot.code'].search(
                [('code', '=', self.l10n_pe_withhold_code)]).percentage
        else:
            self.l10n_pe_withhold_percentage = 0.0
