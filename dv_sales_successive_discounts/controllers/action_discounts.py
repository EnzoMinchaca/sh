from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class DiscountApprovalController(http.Controller):

    @http.route('/discount/approve/<int:sale_order_id>', type='http', auth='user', website=True)
    def approve_discount(self, sale_order_id):

        sale_order = request.env['sale.order'].sudo().browse(sale_order_id)

        for sale in sale_order.sale_successive_discounts:
            sale.action_apply_other_discount()

        sale_order.sale_successive_discounts.write({'state': 'confirmed'})

        sale_order.write({'state_invoice':'approved',})

        return request.redirect('/web#id=%d&view_type=form&model=sale.order' % (sale_order_id))

    @http.route('/discount/reject/<int:sale_order_id>', type='http', auth='user')
    def reject_discount(self, sale_order_id):
        
        sale_order = request.env['sale.order'].sudo().browse(sale_order_id)
        sale_order.write({
            'state_invoice':'rejected'
        })

        for discount in sale_order.sale_successive_discounts:
            discount.write({
                'state':'refused'
            })

        return request.redirect('/web#id=%d&view_type=form&model=sale.order' % (sale_order_id))