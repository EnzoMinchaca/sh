# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, get_lang
from odoo.tools.float_utils import float_compare, float_round

class PurchaseRequestLine(models.Model):
    _name = 'purchase.request.line'

    name = fields.Text(
        string='Descripción', required=True, compute='_compute_price_unit_and_date_planned_and_name', store=True, readonly=False)
    purchase_id = fields.Many2one('purchase.request', string='Solicitud de compra', required=True)
    product_id = fields.Many2one('product.product', string='Producto', domain=[('purchase_ok', '=', True)], change_default=True, index='btree_not_null')
    product_qty = fields.Float(string='Cantidad', required=True, readonly=False)
    product_uom = fields.Many2one('uom.uom', string='UdM', domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    partner_id = fields.Many2one('res.partner', string='Proveedor recomendado', required=True)
    account_analytic_id = fields.Many2one('account.analytic.account', 'SKU')
    account_id = fields.Many2one('account.account', 'Cuenta contable')
    date_order = fields.Datetime('Fecha límite')
    date_planned = fields.Datetime('Fecha esperada')
    user_id = fields.Many2one('res.users', 'Responsable', default=lambda self: self.env.user)
    taxes_id = fields.Many2many('account.tax', string='Impuestos', context={'active_test': False})
    company_id = fields.Many2one('res.company', related='purchase_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='purchase_id.currency_id', store=True, readonly=True)
    state = fields.Selection(related='purchase_id.state', store=True, readonly=True)
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False)
    discount = fields.Float(
        string="Descuento (%)",
        compute='_compute_price_unit_and_date_planned_and_name',
        store=True, readonly=False)
    #Precios
    price_unit = fields.Float(
        string='Precio unitario', required=True)
    price_unit_discounted = fields.Float('Unit Price (Discounted)', compute='_compute_price_unit_discounted')

    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Impuesto', store=True)
    
    #Descripción
    def _get_product_purchase_description(self, product_lang):
        self.ensure_one()
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase

        return name
    
    @api.depends('product_qty', 'product_uom', 'company_id')
    def _compute_price_unit_and_date_planned_and_name(self):
        for line in self:
            if not line.product_id or not line.company_id:
                continue
            # params = {'purchase_id': line.purchase_id}
            # seller = line.product_id._select_seller(
            #     partner_id=line.partner_id,
            #     quantity=line.product_qty,
            #     date=line.purchase_id.date_order and line.purchase_id.date_order.date() or fields.Date.context_today(line),
            #     uom_id=line.product_uom,
            #     params=params)
            
            # # If not seller, use the standard price. It needs a proper currency conversion.
            # if not seller:
            #     unavailable_seller = line.product_id.seller_ids.filtered(
            #         lambda s: s.partner_id == line.partner_id)
            #     if not unavailable_seller and line.price_unit and line.product_uom == line._origin.product_uom:
            #         # Avoid to modify the price unit if there is no price list for this partner and
            #         # the line has already one to avoid to override unit price set manually.
            #         continue
            #     po_line_uom = line.product_uom or line.product_id.uom_po_id
            #     price_unit = line.env['account.tax']._fix_tax_included_price_company(
            #         line.product_id.uom_id._compute_price(line.product_id.standard_price, po_line_uom),
            #         line.product_id.supplier_taxes_id,
            #         line.taxes_id,
            #         line.company_id,
            #     )
            #     price_unit = line.product_id.cost_currency_id._convert(
            #         price_unit,
            #         line.currency_id,
            #         line.company_id,
            #         line.date_order or fields.Date.context_today(line),
            #         False
            #     )
            #     line.price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places, self.env['decimal.precision'].precision_get('Product Price')))
            #     continue

            # price_unit = line.env['account.tax']._fix_tax_included_price_company(seller.price, line.product_id.supplier_taxes_id, line.taxes_id, line.company_id) if seller else 0.0
            # price_unit = seller.currency_id._convert(price_unit, line.currency_id, line.company_id, line.date_order or fields.Date.context_today(line), False)
            # price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places, self.env['decimal.precision'].precision_get('Product Price')))
            # line.price_unit = seller.product_uom._compute_price(price_unit, line.product_uom)
            # line.discount = seller.discount or 0.0
            if line.product_id:
                line.name = line._get_product_purchase_description(line.product_id.product_tmpl_id)
            else:
                line.name = ''
            
            
    
    @api.onchange('account_analytic_id')
    def _onchange_account_analytic_id(self):
        for record in self:
            if record.account_analytic_id:
                account = record.env['account.account'].search(
                    [
                        ('account_analytic_id', '=', record.account_analytic_id.id)
                    ], limit=1)
                record.account_id = account.id
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.product_id:
            return
        self.product_qty = 1.0
        self.price_unit = self.product_id.standard_price
        self._product_id_change()
    
    def _product_id_change(self):
        if not self.product_id:
            return

        self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
        product_lang = self.product_id.with_context(
            lang=get_lang(self.env, self.partner_id.lang).code,
            partner_id=self.partner_id.id,
            company_id=self.company_id.id,
        )
        self.name = self._get_product_purchase_description(product_lang)

        self.taxes_id = self.product_id.supplier_taxes_id.filtered(
            lambda r: not self.company_id or r.company_id == self.company_id)
    
    @api.depends('product_qty', 'price_unit', 'taxes_id', 'discount')
    def _compute_amount(self):
        for line in self:
            tax_results = self.env['account.tax']._compute_taxes([line._convert_to_tax_base_line_dict()])
            totals = next(iter(tax_results['totals'].values()))
            amount_untaxed = totals['amount_untaxed']
            amount_tax = totals['amount_tax']

            line.update({
                'price_subtotal': amount_untaxed,
                'price_tax': amount_tax,
                'price_total': amount_untaxed + amount_tax,
            })
    
    def _convert_to_tax_base_line_dict(self):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.partner_id,
            currency=self.purchase_id.currency_id,
            product=self.product_id,
            taxes=self.taxes_id,
            price_unit=self.price_unit,
            quantity=self.product_qty,
            discount=self.discount,
            price_subtotal=self.price_subtotal,
        )
    
    @api.depends('discount', 'price_unit')
    def _compute_price_unit_discounted(self):
        for line in self:
            line.price_unit_discounted = line.price_unit * (1 - line.discount / 100)