# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _inherit = ['portal.mixin', 'product.catalog.mixin', 'mail.thread', 'mail.activity.mixin']
    _rec_names_search = ['name', 'partner_ref']
    _order = 'priority desc, id desc'

    name = fields.Char(string='Referencia de solicitud', index='trigram', copy=False, default='New')
    priority = fields.Selection(
        [('0', 'Normal'), ('1', 'Urgent')], 'Priority', default='0', index=True)
    partner_id = fields.Many2one('res.partner', string='Proveedor recomendado', index=True)
    partner_ref = fields.Char(string='Referencia de proveedor')
    state = fields.Selection([
        ('pending', 'Pendiente'),
        ('process', 'En proceso'),
        ('done', 'Recibido'),
        ('cancel', 'Rechazado'),
    ], string='Estado', readonly=True, index=True, copy=False, default='pending', tracking=True)
    date_order = fields.Datetime('Fecha límite', required=True, index=True, copy=False, default=fields.Datetime.now)
    confirmation_date = fields.Datetime('Fecha de confirmación', readonly=True, index=True)
    area_id = fields.Many2one('hr.department', 'Departamento', index=True)
    company_id = fields.Many2one('res.company', 'Compañia', required=True, index=True, default=lambda self: self.env.company.id)
    user_id = fields.Many2one('res.users', 'Responsable', index=True, default=lambda self: self.env.user, tracking=True)
    currency_id = fields.Many2one('res.currency', 'Moneda', required=True,
        default=lambda self: self.env.company.currency_id.id)
    request_line = fields.One2many('purchase.request.line', 'purchase_id', string='Lineas de solicitud', copy=True)
    tax_country_id = fields.Many2one(
        comodel_name='res.country',
        compute='_compute_tax_country_id',
        compute_sudo=True,)
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Posición fiscal', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", copy=False)
    notes = fields.Html('Notas y observaciones', copy=False)
    #Precios
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', tracking=True)
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all')
    tax_totals = fields.Binary(compute='_compute_tax_totals', exportable=False)

    purchase_order_ids = fields.Many2many('purchase.order', string='Órdenes de Compra', copy=False)
    count_purchase_order = fields.Integer(
        string='Cantidad de ordenes',
        compute='compute_purchase_orders',
        store=True
    )

    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.request') or '/'
        return super(PurchaseRequest, self).create(vals)
    
    @api.depends('company_id.account_fiscal_country_id', 'fiscal_position_id.country_id', 'fiscal_position_id.foreign_vat')
    def _compute_tax_country_id(self):
        for record in self:
            if record.fiscal_position_id.foreign_vat:
                record.tax_country_id = record.fiscal_position_id.country_id
            else:
                record.tax_country_id = record.company_id.account_fiscal_country_id
    
    @api.depends('request_line.price_total')
    def _amount_all(self):
        for order in self:
            request_lines = order.request_line.filtered(lambda x: not x.display_type)

            if order.company_id.tax_calculation_rounding_method == 'round_globally':
                tax_results = self.env['account.tax']._compute_taxes([
                    line._convert_to_tax_base_line_dict()
                    for line in request_lines
                ])
                totals = tax_results['totals']
                amount_untaxed = totals.get(order.currency_id, {}).get('amount_untaxed', 0.0)
                amount_tax = totals.get(order.currency_id, {}).get('amount_tax', 0.0)
            else:
                amount_untaxed = sum(request_lines.mapped('price_subtotal'))
                amount_tax = sum(request_lines.mapped('price_tax'))

            order.amount_untaxed = amount_untaxed
            order.amount_tax = amount_tax
            order.amount_total = order.amount_untaxed + order.amount_tax
    
    @api.depends_context('lang')
    @api.depends('request_line.taxes_id', 'request_line.price_subtotal', 'amount_total', 'amount_untaxed')
    def _compute_tax_totals(self):
        for order in self:
            request_lines = order.request_line.filtered(lambda x: not x.display_type)
            order.tax_totals = self.env['account.tax']._prepare_tax_totals(
                [x._convert_to_tax_base_line_dict() for x in request_lines],
                order.currency_id or order.company_id.currency_id,
            )
    
    def create_purchase_orders(self):
        PurchaseOrder = self.env['purchase.order']
        PurchaseOrderLine = self.env['purchase.order.line']
        purchase_orders = []

        # Agrupar las líneas por partner_id
        grouped_lines = {}
        for line in self.request_line:
            if line.partner_id not in grouped_lines:
                grouped_lines[line.partner_id] = []
            grouped_lines[line.partner_id].append(line)

        # Crear una orden de compra por cada partner_id
        for partner, lines in grouped_lines.items():
            # Obtener el mínimo date_order y date_planned de las líneas
            min_date_order = min(line.date_order for line in lines if line.date_order)
            min_date_planned = min(line.date_planned for line in lines if line.date_planned)

            # Crear la orden de compra
            purchase_order = PurchaseOrder.create({
                'partner_id': partner.id,
                'date_order': min_date_order,
                'date_planned': min_date_planned,
                'company_id': self.company_id.id,
                'currency_id': self.currency_id.id,
                'origin': self.name,
                'purchase_request_id': self.id,
            })

            # Crear las líneas de la orden de compra
            for line in lines:
                PurchaseOrderLine.create({
                    'order_id': purchase_order.id,
                    'product_id': line.product_id.id,
                    'product_qty': line.product_qty,
                    'price_unit': line.price_unit,
                    'date_planned': line.date_planned or self.date_order,
                    'taxes_id': [(6, 0, line.taxes_id.ids)],
                    'name': line.name,
                    'account_analytic_id': line.account_analytic_id.id,
                    'account_id': line.account_id.id,
                })
            purchase_orders.append(purchase_order.id)
            purchase_order.sku = lines[0].account_analytic_id.id

        # Almacenar las órdenes de compra en el campo Many2many
        self.write({
            'purchase_order_ids': [(6, 0, purchase_orders)],
            'state': 'process',
            'confirmation_date': fields.Datetime.now()
        })
    
    def action_cancel(self):
        self.write({'state': 'cancel'})
    
    def check_done_state(self):
        for request in self:
            # Verificar si todas las órdenes de compra están en estado 'purchase'
            all_confirmed = all(order.state == 'purchase' for order in request.purchase_order_ids)

            if not all_confirmed:
                return  # Si alguna orden no está confirmada, no seguimos

            # Si todas las órdenes están confirmadas, ahora verificamos los pickings
            all_done = True
            for order in request.purchase_order_ids:
                # Verificar que todos los pickings de la orden estén en 'done'
                if not all(picking.state == 'done' for picking in order.picking_ids):
                    all_done = False
                    break  # Si encontramos algún picking que no esté en 'done', detenemos el proceso

            # Si todas las órdenes están confirmadas y todos los pickings están en 'done', cambiamos el estado
            if all_done:
                request.write({'state': 'done'})
    
    @api.depends('purchase_order_ids')
    def compute_purchase_orders(self):
        for request in self:
            request.count_purchase_order = len(request.purchase_order_ids)
    
    #Metodo para el botón de abrir pagos relacionados
    def action_open_related_orders(self):
        self.ensure_one()
        orders = self.mapped('purchase_order_ids')    
        action = self.env["ir.actions.actions"]._for_xml_id("purchase.purchase_rfq")
        if len(orders) > 0:
            action['domain'] = [('id', 'in', orders.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

