from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class SuccessiveDiscounts(models.Model):
    _name = 'sale.successive.discounts'
    _description = 'Descuentos Sucesivos en las Ventas'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Asegúrate de incluir esto

    sale_order_id = fields.Many2one('sale.order', string='Orden de Venta')

    sale_order_line_id = fields.Many2one('sale.order.line', string='Sale Order Line')
    original_price = fields.Float(string="Precio Lista Original")

    first_discount = fields.Integer(string="Descuento 1")
    first_price = fields.Float(digits=(16, 4), compute="_compute_first_price", store=True)

    second_discount = fields.Integer(string="Descuento 2")
    second_price = fields.Float(digits=(16, 4), compute="_compute_second_price", store=True)

    third_discount = fields.Integer(string="Descuento 3")
    third_price = fields.Float(digits=(16, 4), compute="_compute_third_price", store=True)

    final_price = fields.Float(string="Precio Lista Final", digits=(16, 4), compute="_compute_final_price", store=True)
    first_discount_amount = fields.Float(compute="_compute_first_price")

    second_discount_amount = fields.Float(compute="_compute_second_price")
    third_discount_amount = fields.Float(compute="_compute_third_price")

    seller_id = fields.Many2one('res.partner', string="Vendedor")

    state = fields.Selection(
        selection=[
            ("draft", "Borrador"),
            ("on_hold", "En Espera"),
            ("confirmed", "Confirmado"),
            ("refused", "Rechazado"),
        ],
        string="Estado",
        readonly=True, copy=False)


    @api.model
    def create_activitiy(self, type, note):
        # Crear una actividad
        activity = self.env['mail.activity']
        
        # Definir los parámetros de la actividad
        vals_activity = {
            'res_model_id': self.env['ir.model']._get('sale.successive.discounts').id,
            'res_id': self.id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'summary': f"Descuento ha sido {type}", 
            'user_id': self.env.user.id,
            'note': note
        }
        
        # Crear la actividad
        activity.create(vals_activity)

    # Acá estan las validaciones
    @api.onchange('first_discount', 'second_discount', 'third_discount')
    def _onchange_discount_percentage(self):
        # 
        if self.first_discount > 30:
            self.first_discount = 30

        if self.second_discount > 50:
            self.second_discount = 50

        if self.third_discount > 50:
            self.third_discount = 50

    @api.constrains('first_discount', 'second_discount', 'third_discount')
    def _check_discounts(self):
        for record in self:
            if not (0 <= record.first_discount <= 30):
                raise ValidationError("El 'Descuento 1' debe estar entre 0 y 30.")
            if not (0 <= record.second_discount <= 50):
                raise ValidationError("El 'Descuento 2' debe estar entre 0 y 50.")
            if not (0 <= record.third_discount <= 50):
                raise ValidationError("El 'Descuento 3' debe estar entre 0 y 50.")

            if record.first_discount == 0 and (record.second_discount > 0 or record.third_discount > 0):
                raise ValidationError("El 'Descuento 1' no debe ser 0 cuando hay valor en los otros descuentos.")
            if record.second_discount == 0 and record.third_discount > 0:
                raise ValidationError("El 'Descuento 2' no debe ser 0 cuando hay valor en el 'Decuento 3'.")

    @api.depends('first_discount', 'original_price')
    def _compute_first_price(self):
        for res in self:
            res.first_discount_amount = res._calculate_discount_amount(res.original_price, res.first_discount)
            res.first_price = res._calculate_discounted_price(res.original_price, res.first_discount)

    @api.depends('second_discount', 'first_price')
    def _compute_second_price(self):
        for res in self:
            res.second_discount_amount = res._calculate_discount_amount(res.first_price, res.second_discount)
            res.second_price = res._calculate_discounted_price(res.first_price, res.second_discount)

    @api.depends('third_discount', 'second_price')
    def _compute_third_price(self):
        for res in self:
            res.third_discount_amount = res._calculate_discount_amount(res.second_price, res.third_discount)
            res.third_price = res._calculate_discounted_price(res.second_price, res.third_discount)

    @api.onchange('first_discount', 'second_discount', 'third_discount')
    def _onchange_discount_and_state(self):
        if self.state and self.state != 'draft':
            self.state = 'draft'

    # Función para calcular el monto de descuento
    def _calculate_discount_amount(self, price, discount):
        if discount:
            return price * (discount / 100)
        else:
            return 0.0000

    # Función para calcular el precio con el descuento aplicado
    def _calculate_discounted_price(self, price, discount):
        if discount:
            return price * (1 - discount / 100)
        else:
            return price

    @api.depends('original_price', 'first_discount_amount', 'second_discount_amount', 'third_discount_amount')
    def _compute_final_price(self):
        for res in self:
            price = self.original_price
            first_price = self.first_discount_amount
            second_price = self.second_discount_amount
            third_price = self.third_discount_amount

            res.final_price = price - first_price - second_price - third_price

    def action_apply_first_discount(self):
        sale_order_line = self.env['sale.order.line'].browse(self.sale_order_line_id.id)

        sale_order_line.write({'price_unit': round(self.final_price, 2)}) 

        return {'type': 'ir.actions.act_window_close'}

    def action_save_date(self):
        self.ensure_one()

        if self.second_discount > 0:
            self.second_discount = self.second_discount

        if self.third_discount > 0:
            self.third_discount = self.third_discount
        
        self.write({'state':'on_hold'})

        self.sale_order_line_id.order_id.write(({
            'state_invoice':'draft'
        }))

        return {
            'type': 'ir.actions.act_window',
            'name': 'Descuentos Sucesivos',
            'res_model': 'sale.successive.discounts',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_apply_other_discount(self):

        sale_order_line = self.env['sale.order.line'].browse(self.sale_order_line_id.id)
        sale_order_line.write({'price_unit': round(self.final_price, 2)}) 
        self.write({'state': False})
        return {'type': 'ir.actions.act_window_close'}