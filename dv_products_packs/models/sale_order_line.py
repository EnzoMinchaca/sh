from datetime import timedelta
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.tools import float_compare
from odoo.exceptions import UserError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    #Filtro de rutas
    route_filtered_ids = fields.Many2many(
        'stock.route', 
        string='Available Routes', 
        compute='_compute_route_filtered_ids'
    )
    selected_route_id = fields.Many2one('stock.route', 
        string='Selected Route', 
        domain=lambda self: [('id', 'in', self.route_filtered_ids.ids)])

    @api.depends('product_id.route_ids')
    def _compute_route_filtered_ids(self):
        for line in self:
            line.route_filtered_ids = line.product_id.route_ids
    
    #Separacion de productos del pack por picking
    @api.onchange('selected_route_id')
    def _onchange_selected_route_id(self):
        if self.selected_route_id:
            self.route_id = self.selected_route_id
            # print("Route ID:", self.route_id)
        else:
            self.route_id = False
    