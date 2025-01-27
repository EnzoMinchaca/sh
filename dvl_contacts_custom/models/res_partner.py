from odoo import api, models, _, fields
from odoo.tools import get_lang, SQL
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'
    _order = "is_favorite desc"
    
    @api.model
    def _search_is_favorite(self, operator, value):
        if operator not in ['=', '!='] or not isinstance(value, bool):
            raise NotImplementedError(_('Operation not supported'))
        return [('favorite_user_ids', 'in' if (operator == '=') == value else 'not in', self.env.uid)]

    def _compute_is_favorite(self):
        for partner in self:
            partner.is_favorite = self.env.user in partner.favorite_user_ids

    def _inverse_is_favorite(self):
        favorite_partners = not_fav_partners = self.env['res.partner'].sudo()
        for partner in self:
            if self.env.user in partner.favorite_user_ids:
                favorite_partners |= partner
            else:
                not_fav_partners |= partner

        # User has no write access for partners
        not_fav_partners.write({'favorite_user_ids': [(4, self.env.uid)]})
        favorite_partners.write({'favorite_user_ids': [(3, self.env.uid)]})

    data_line_ids = fields.One2many('data.line', 'partner_id', string='Datos', store=True)
    contact_line_ids = fields.One2many('contact.line', 'partner_id', string='Contactos', store=True)
    ubicacion_line_ids = fields.One2many('ubicacion.line', 'partner_id', string='Ubicación', store=True)
    accesos_line_ids = fields.One2many('accesos.line', 'partner_id', string='Accesos', store=True)
    class_type = fields.Selection([
        ('cliente', 'Cliente'),
        ('proveedor', 'Proveedor'),
        ('externo', 'Externo'),
        ('interno', 'Interno')
    ], string='Tipo', store=True, default='cliente')
    class_types = fields.Many2many('contact.types', string='Tipos')
    is_update = fields.Boolean(string='Actualizado', store=True)
    favorite_user_ids = fields.Many2many(
        'res.users', 'partner_favorite_user_rel', 'partner_id', 'user_id',
        default=lambda self: [(6, 0, [self.env.uid])],
        string='Favorite Users'
    )
    is_favorite = fields.Boolean(
        compute='_compute_is_favorite', 
        inverse='_inverse_is_favorite', 
        search='_search_is_favorite',
        compute_sudo=True, 
        string='Is Favorite'
    )
    sequence = fields.Integer(default=10)
    
    is_interno = fields.Boolean(string='Es Interno', store=True)
    is_externo = fields.Boolean(string='Es Externo', store=True)
    is_cliente = fields.Boolean(string='Es Cliente', store=True, default=True)
    is_proveedor = fields.Boolean(string='Es Proveedor', store=True)
    update_flag = fields.Boolean(compute='_compute_update_flag', store=True)
    
    #Compute para actualizar los campos de tipo de contacto
    @api.depends('class_type')
    def _compute_update_flag(self):
        for record in self:
            contact_types = self.env['contact.types']
            if record.class_type == 'cliente':
                record.is_cliente = True
                record.class_types = contact_types.search([('name', 'ilike', 'Cliente')], limit=1)
            elif record.class_type == 'proveedor':
                record.is_proveedor = True
                record.class_types = contact_types.search([('name', 'ilike', 'Proveedor')], limit=1)
            elif record.class_type == 'externo':
                record.is_externo = True
                record.class_types = contact_types.search([('name', 'ilike', 'Externo')], limit=1)
            elif record.class_type == 'interno':
                record.is_interno = True
                record.class_types = contact_types.search([('name', 'ilike', 'Interno')], limit=1)
            record.update_flag = True

    #Método para asignar todos los permisos al creador de usuarios
    def asign_master_create_access(self):
        selectec_partners = self.env['res.partner'].browse(self._context.get('active_ids', []))
        for partner in selectec_partners:
            partner.is_cliente = True
            partner.is_proveedor = True
            partner.is_externo = True
            partner.is_interno = True
    
    #Método para forzar la actualización del tipo en data line
    def force_update_data_line(self):
        partners = self.search([])
        for partner in partners:
            #Actualiza el tipo en data line
            # for line in partner.data_line_ids:
            #     line.compute_data_lines_types()
            if partner.data_line_ids:
                first_data_line = partner.data_line_ids[0]
                partner.class_types = first_data_line.tipo_id

    @api.model
    def migrate_class_type_to_class_types(self):
        contact_types_model = self.env['contact.types']
        partners = self.search([])
        for partner in partners:
            # Para `class_types` en `res.partner`
            if partner.class_type:
                class_type_record = contact_types_model.search([('name', '=', partner.class_type.capitalize())], limit=1)
                if class_type_record:
                    partner.write({
                        'class_types': [(4, class_type_record.id)],
                        'is_update': True
                    })
                if partner.data_line_ids:
                    for line in partner.data_line_ids:
                        line.write({
                            'tipo_id': [(4, class_type_record.id)]
                        })
                else:
                    partner.write({
                        'is_cliente': True
                    })
    
    @api.model
    def create(self, vals):
        if not vals.get('data_line_ids'):
            vals['is_cliente'] = True 
        partner = super(ResPartner, self).create(vals)
        return partner

    @api.onchange('data_line_ids')
    def _onchange_data_lines(self):
        if self.data_line_ids:
            # Ordenar data_line_ids por sequence
            sorted_lines = sorted(self.data_line_ids, key=lambda line: line.sequence)
            if sorted_lines:
                self.vat = sorted_lines[0].vat
                self.l10n_latam_identification_type_id = sorted_lines[0].tipo_documento
                self.email = sorted_lines[0].email or self.email
                self.mobile = sorted_lines[0].mobile or self.mobile
                self.category_id = sorted_lines[0].category_id
                self.class_type = sorted_lines[0].tipo or 'cliente'

                if self.company_type == "company":
                    self.name = sorted_lines[0].razon_social
                else:
                    self.name = sorted_lines[0].razon_social

                # Modificado
                if sorted_lines[0].tipo_id:
                    self.class_types = [(6, 0, sorted_lines[0].tipo_id.ids)]
                else:
                    default_type = self.env['contact.types'].search([('name', '=', 'Cliente')], limit=1)
                    if default_type:
                        self.class_types = [(4, default_type.id)]
                    else:
                        self.class_types = [(5, 0, 0)]  # Limpiar si no se encuentra "Cliente"
                # Obtener los nombres de los tipos asociados a class_types
                class_type_names = self.class_types.mapped('name')
                # Validación de combinaciones permitidas
                if len(class_type_names) > 1:
                    if set(class_type_names) == {'Cliente', 'Proveedor'}:
                        pass
                    else:
                        # Combinación no permitida
                        last_type = class_type_names[-1]  # Obtener el último tipo
                        last_type_record = self.env['contact.types'].search([('name', '=', last_type)], limit=1)
                        # Eliminar el tipo no permitido de class_types
                        self.class_types = [(3, last_type_record.id)]
                        # Eliminar también el tipo en tipo_id de cada línea
                        for line in self.data_line_ids:
                            line.tipo_id = [(3, last_type_record.id)]  # Eliminar el tipo en tipo_id
                        # Mostrar un mensaje al usuario
                        return {
                            'warning': {
                                'title': "Combinación de tipos inválida",
                                'message': "Las únicas combinaciones permitidas son:\n"
                                            "- Un solo tipo (Cliente, Proveedor, Externo, Interno)\n"
                                            "- Cliente y Proveedor juntos.\n"
                                            "Se ha eliminado el tipo: {}".format(last_type)
                            }
                        }
                    
                # Verificar si ninguno de los tipos asociados es "Interno" o "Externo"
                if not any(name in ['Interno', 'Externo'] for name in class_type_names):
                    if self.company_type == "company":
                        self.name = sorted_lines[0].razon_social
                else:
                    self.name = sorted_lines[0].razon_social

                # Imprimir los tipos actualizados después de cualquier eliminación
                updated_class_type_names = self.class_types.mapped('name')

                # Configurar los booleanos basados en updated_class_type_names
                self.is_interno = 'Interno' in updated_class_type_names
                self.is_externo = 'Externo' in updated_class_type_names
                self.is_cliente = 'Cliente' in updated_class_type_names
                self.is_proveedor = 'Proveedor' in updated_class_type_names

    @api.onchange('contact_line_ids')
    def _onchange_contact_lines(self):
        if self.contact_line_ids:
            sorted_lines = sorted(self.contact_line_ids, key=lambda line: line.sequence)
            if sorted_lines:
                if self.company_type != "company":
                    self.name = self.contact_line_ids[0].name
                self.email = self.contact_line_ids[0].email
                self.phone = self.contact_line_ids[0].phone
                self.mobile = self.contact_line_ids[0].mobile
                self.function = self.contact_line_ids[0].funcion

    @api.onchange('ubicacion_line_ids')
    def _onchange_ubicacion_lines(self):
        if self.ubicacion_line_ids:
            sorted_lines = sorted(self.ubicacion_line_ids, key=lambda line: line.sequence)
            if sorted_lines:
                self.type = self.ubicacion_line_ids[0].tipo
                self.street = self.ubicacion_line_ids[0].contact_address
                self.ref = self.ubicacion_line_ids[0].ref
                self.city_id = self.ubicacion_line_ids[0].ciudad
                self.l10n_pe_district = self.ubicacion_line_ids[0].distrito
                self.country_id = self.ubicacion_line_ids[0].pais_id
    
    def transfer_data_to_lines(self):
        selected_invoices = self.env['res.partner'].browse(self._context.get('active_ids', []))
        if not selected_invoices:
            selected_invoices = self
        for record in selected_invoices.filtered(lambda record: record.is_update == False):
            # Crear data_line
            data_line = self.env['data.line'].create({
                'sequence': 1,
                'vat': record.vat,
                'tipo_documento': record.l10n_latam_identification_type_id.id,
                'tipo': record.class_type,  
                # Nuevo campo: tipo_id, pasando los IDs de los tipos relacionados en class_types
                'tipo_id': [(6, 0, record.class_types.ids)],
                'partner_id': record.id,
                'razon_social': record.name if record.company_type == "company" else False,
            })
            # Crear contact_line
            contact_line = self.env['contact.line'].create({
                'sequence': 1,
                'name': record.name if record.company_type == "person" else False,
                'email': record.email,
                'phone': record.phone,
                'mobile': record.mobile,
                'funcion': record.function,
                'partner_id': record.id,
            })
            # Crear ubicacion_line
            ubicacion_line = self.env['ubicacion.line'].create({
                'sequence': 1,
                'tipo': record.type,
                'contact_address': record.street,
                'ref': record.ref,
                'ciudad': record.city_id.id,
                'distrito': record.l10n_pe_district.id,
                'pais_id': record.country_id.id,
                'partner_id': record.id,
            })
            record.is_update = True
    
    def write(self, vals):
        if 'is_favorite' in vals:
            vals.pop('is_favorite')
            self._fields['is_favorite'].determine_inverse(self)
        return super(ResPartner, self).write(vals)

    def _order_field_to_sql(self, alias, field_name, direction, nulls, query):
        if field_name == 'is_favorite':
            sql_field = SQL(
                "%s IN (SELECT partner_id FROM partner_favorite_user_rel WHERE user_id = %s)",
                SQL.identifier(alias, 'id'), self.env.uid,
            )
            return SQL("%s %s %s", sql_field, direction, nulls)
        return super(ResPartner, self)._order_field_to_sql(alias, field_name, direction, nulls, query)

    def toggle_favorite(self):
        favorite_partners = not_fav_partners = self.env['res.partner'].sudo()
        for partner in self:
            if self.env.user in partner.favorite_user_ids:
                favorite_partners |= partner
            else:
                not_fav_partners |= partner

        # User has no write access for partners
        not_fav_partners.write({'favorite_user_ids': [(4, self.env.uid)]})
        favorite_partners.write({'favorite_user_ids': [(3, self.env.uid)]})