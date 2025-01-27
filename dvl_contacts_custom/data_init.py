from odoo import api, SUPERUSER_ID

def _set_default_partner_values(env):
    # Buscar el partner de admin
    print("Funciona!")
    admin_partner = env['res.partner'].browse(3)  # ID de admin
    if admin_partner:
        admin_partner.write({
            'is_cliente': True,
            'is_proveedor': True,
            'is_externo': True,
            'is_interno': True
        })
    
    # Buscar el partner de OdooBot por id
    odoobot_partner = env['res.partner'].browse(2)  # ID de OdooBot
    if odoobot_partner:
        odoobot_partner.write({
            'is_cliente': True,
            'is_proveedor': True,
            'is_externo': True,
            'is_interno': True
        })

# Llamar a la función en el post-init del módulo
def post_init_hook(env):
    _set_default_partner_values(env)


