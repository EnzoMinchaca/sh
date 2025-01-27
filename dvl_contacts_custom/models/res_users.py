from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def create(self, vals):
        user = super(ResUsers, self).create(vals)
        user._update_partner_group()
        return user

    def write(self, vals):
        result = super(ResUsers, self).write(vals)
        self._update_partner_group()
        return result

    def _update_partner_group(self):
        for user in self:
            partner = user.partner_id
            if not partner:
                continue

            # Eliminar todos los tipos anteriores y resetear los booleanos
            partner.write({
                'class_types': [(5, 0, 0)],  # Eliminar todos los tipos existentes
                'is_cliente': False,
                'is_proveedor': False,
                'is_interno': False,
                'is_externo': False,
            })

            # Bandera para verificar si el usuario tiene algún grupo específico asignado
            group_assigned = False

            # Asignar booleanos al admin
            if user.has_group('dvl_contacts_custom.group_partner_admin'):
                partner.is_cliente = True
                partner.is_proveedor = True
                partner.is_interno = True
                partner.is_externo = True
                group_assigned = True

            # Si el usuario no pertenece a ningún grupo específico, se asigna como Cliente por defecto
            if not group_assigned:
                partner.is_cliente = True
