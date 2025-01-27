from odoo import models,fields,api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_successive_discounts = fields.One2many('sale.successive.discounts','sale_order_id',string='Descuentos Sucesivos')

    state_invoice = fields.Selection(
        selection=[
            ('init','Init'),
            ('draft','Draft'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ],
        help="Campo de selección para indicar el estado de la solicitud de descuento",
        default='init'
    )

    def create_activity(self, type, note):
        for record in self:
            vals_activity = {
                'res_model_id': self.env['ir.model']._get('sale.order').id,
                'res_id': record.id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': f"Descuento ha sido {type}",
                'user_id': self.env.user.id,
                'note': note,
                'activity_category': 'default',
            }
            self.env['mail.activity'].create(vals_activity)


    def line_discounts(self):
        for order in self:
            discount_ids = []

            for line in order.order_line:
                discount = self.env['sale.successive.discounts'].search([
                    ('sale_order_line_id', '=', line.id),
                    ('state', '=', 'on_hold')
                ])
                discount_ids.extend(discount.ids)

            order.sale_successive_discounts = [(6, 0, discount_ids)]
        return

    # Este método debe de crear un correo electronico
    def action_send_request_discounts(self):
        self.ensure_one()

        self.line_discounts()
        
        template_id = self.env.ref('dv_sales_successive_discounts.email_template_discounts').id

        if template_id:
            self.env['mail.template'].browse(template_id).send_mail(self.id, force_send=True)

        self.state_invoice = 'pending'
    
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'flags': {'reload': True},
        }

    
    def action_update_price_sale_order_line(self):
        
        self.state_invoice = 'pending'

        for line in self.sale_successive_discounts:
            line.action_apply_other_discount()
        
        self.sale_successive_discounts.write({'state': 'confirmed'})

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
        