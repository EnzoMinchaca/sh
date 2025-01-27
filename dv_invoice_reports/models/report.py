from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import base64
from datetime import datetime

class Reports(models.Model):
    _name = 'invoice.report'
    
    name = fields.Char(string="Nuevo Reporte", default="Nuevo Reporte")
    tipo_reporte = fields.Selection(
        selection="_get_tipo_reporte_selection",
        string='Tipo de Reporte'
    )
    cliente = fields.Many2one('res.partner', string='Cliente')
    prod = fields.Many2one('product.product', string='Producto')
    usuario_vendedor = fields.Many2one('res.users', string='Vendedor')
    proveedor = fields.Many2one('res.partner', string='Proveedor')
    origen = fields.Selection([
        ('nacional', 'Nacional'),
        ('extranjero', 'Extranjero')
    ], string='Origen')
    marca_categoria = fields.Many2one('product.category', string="Marca")
    fecha_desde = fields.Date(string="Desde")
    fecha_hasta = fields.Date(string="Hasta")
    is_user_vendedor = fields.Boolean(string="Es vendedor", default=False)
    is_user_comprador = fields.Boolean(string="Es comprador", default=False)

    # Declarando el campo usuario
    user_id = fields.Many2one('res.users', string="Usuario", default=lambda self: self.env.user)
    
    #validacion para la Fechas
    @api.onchange("tipo_reporte")
    def _onchange_tipo_reporte(self):
        if self.tipo_reporte:
            self.cliente = None
            self.prod = None
            self.proveedor = None
            self.origen = None
            self.marca_categoria = None
        if not self.is_user_vendedor:
            self.usuario_vendedor = None
    
    #validacion para la Fechas
    @api.onchange("fecha_desde", "fecha_hasta")
    def _onchange_valid(self):
        if self.fecha_desde and self.fecha_hasta and self.fecha_hasta < self.fecha_desde:
            self.fecha_hasta = False
            return {
                "warning": {
                    "title": "Validación de Fecha",
                    "message": "La Fecha Hasta no puede ser menor que la Fecha Desde.",
                }
            }
    
    #primer metodo en ejecutarse al abrir este modelo
    @api.model
    def default_get(self, fields_list):
        defaults = super(Reports, self).default_get(fields_list)
        user = self.env.user
        #esto es para los usuarios que son vendedores o compradores
        vendedor_group = self.env.ref('dv_invoice_reports.group_vendedor_reportes')
        comprador_group = self.env.ref('dv_invoice_reports.group_comprador_reportes')
        if vendedor_group in user.groups_id:
            defaults['usuario_vendedor'] = user.id
            defaults['is_user_vendedor'] = True
        if comprador_group in user.groups_id:
            defaults['is_user_comprador'] = True
        return defaults
    
    #valido que opciones a mostrar segun el grupo al que pertenece el usuario
    @api.model
    def _get_tipo_reporte_selection(self):
        if self.env.user.has_group('dv_invoice_reports.group_vendedor_reportes'):
            return [
                ('vendedor_marca', 'Vendedor-Marca'),
                ('cliente_producto', 'Cliente-Producto'),
                ('ventas_vendedor', 'Ventas-Vendedor'),
                ('ventas_cliente', 'Ventas-Cliente'),
            ]
        elif self.env.user.has_group('dv_invoice_reports.group_comprador_reportes'):
            return [
                ('compras', 'Compras')
            ]
        else:
            return [
                ('vendedor_marca', 'Vendedor-Marca'),
                ('cliente_producto', 'Cliente-Producto'),
                ('ventas_vendedor', 'Ventas-Vendedor'),
                ('ventas_cliente', 'Ventas-Cliente'),
                ('compras', 'Compras'),
                ('ranking_productos', 'Ranking de Productos'),
            ]
    
    def generate_pdf_report(self, facturas, tipo, clientes, vendedores, productos, marcas, report_data, total_usd_reporte, total_pen_reporte, total_usd_reporte_impuestos, total_pen_reporte_impuestos, total_usd_reporte_valor_impuestos, total_pen_reporte_valor_impuestos):
        if not facturas:
            raise UserError("No se encontraron facturas para generar el reporte.")
        if tipo == 'General':
            template = 'dv_invoice_reports.reporte_filtros_template'
        if tipo == 'Detallado':
            template = 'dv_invoice_reports.reporte_filtros_template_detallado'
        
        try:
            #preparo el pdf
            pdf_content, _ = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                template,
                [self.id], 
                data={
                    'facturas': facturas,
                    'tipo': tipo,
                    'tipo_reporte': self.tipo_reporte,
                    'clientes': clientes,
                    'vendedores': vendedores,
                    'productos': productos,
                    'marcas': marcas,
                    'fecha_inicio': datetime.strptime(str(self.fecha_desde), '%Y-%m-%d').strftime('%d/%m/%Y'),
                    'fecha_fin': datetime.strptime(str(self.fecha_hasta), '%Y-%m-%d').strftime('%d/%m/%Y') ,
                    'fecha_report': datetime.strptime(str(fields.Date.today()), '%Y-%m-%d').strftime('%d/%m/%Y'),
                    'report_data': report_data,
                    'total_usd_reporte': total_usd_reporte,
                    'total_pen_reporte': total_pen_reporte,
                    'total_usd_reporte_impuestos': total_usd_reporte_impuestos,
                    'total_pen_reporte_impuestos': total_pen_reporte_impuestos,
                    'total_usd_reporte_valor_impuestos': total_usd_reporte_valor_impuestos,
                    'total_pen_reporte_valor_impuestos': total_pen_reporte_valor_impuestos
                    }
            )
        except Exception as e:
            raise UserError(f"Error al renderizar el PDF: {str(e)}")

        report_name = f'Reporte_{self.tipo_reporte} - {tipo}.pdf'
        attachment = self.env['ir.attachment'].create({
            'name': report_name,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })
        
        #este es por si el de abajo no llega a funcionar, con este no uso el http.route
        # return {
        #     'type': 'ir.actions.act_url',
        #     'url': f'/web/content/{attachment.id}?filename={report_name}',
        #     'target': 'new', 
        # }
        
        #con esto lo muestro en el navegador para descargarlo desde ahi
        return {
            'type': 'ir.actions.act_url',
            'url': f'/reporte_facturas/download/{attachment.id}',
            'target': 'new',  #abrir en nueva pestaña
        }

    #esto me trae las facturas para todos los tipos
    def facturas_vendedor_marca_cliente_producto(self):
        for record in self:
            facturas = None
            notas_credito = None
            if record.tipo_reporte == 'compras':
                #dominio para facturas de proveedor
                domain = [
                    ('invoice_date', '>=', record.fecha_desde), #solo facturas dentro del rango de fechas indicado
                    ('invoice_date', '<=', record.fecha_hasta),
                    ('move_type', '=', 'in_invoice'),  #solo facturas de proveedor
                    ('state', '=', 'posted'),   #solo facturas posteadas
                ]
                #dominio para notas de credito de proveedor
                domain_notas_credito = [
                    ('invoice_date', '>=', record.fecha_desde),
                    ('invoice_date', '<=', record.fecha_hasta),
                    ('move_type', '=', 'in_refund'),  #solo notas de crédito de proveedor
                    ('state', '=', 'posted'),
                    #('edi_state', '=', 'sent')     #aca no tiene facturacion electronica
                ]
                #si hay un proveedor seleccionado
                if record.proveedor:
                    domain.append(('partner_id', '=', record.proveedor.id))
                    domain_notas_credito.append(('partner_id', '=', record.proveedor.id))
                facturas = self.env['account.move'].search(domain)
                notas_credito = self.env['account.move'].search(domain_notas_credito)
                #facturas y nc con filtro de producto, sino saco todas las facturas y nc que no tienen ningun producto
                if record.prod:
                    facturas_prod = facturas.filtered(lambda inv: any(line.product_id.id == record.prod.id for line in inv.line_ids))
                    facturas = facturas_prod
                    facturas_nc_prod = notas_credito.filtered(lambda inv: any(line.product_id.id == record.prod.id for line in inv.line_ids))
                    notas_credito = facturas_nc_prod
                else:
                    facturas_prod = facturas.filtered(lambda inv: any(line.product_id.id != None for line in inv.line_ids))
                    facturas = facturas_prod
                    facturas_nc_prod = notas_credito.filtered(lambda inv: any(line.product_id.id != None for line in inv.line_ids))
                    notas_credito = facturas_nc_prod
                #filtro segun el origen del proveedor
                if record.origen:
                    if record.origen == 'nacional':
                        facturas = facturas.filtered(
                            lambda inv: inv.partner_id.l10n_latam_identification_type_id.name == 'RUC'
                        )
                        notas_credito = notas_credito.filtered(
                            lambda inv: inv.partner_id.l10n_latam_identification_type_id.name == 'RUC'
                        )
                    #extranjero son todos aquellos que son distintos a RUC en su tipo de documento
                    elif record.origen == 'extranjero':
                        facturas = facturas.filtered(
                            lambda inv: inv.partner_id.l10n_latam_identification_type_id.name not in ['RUC']
                        )
                        notas_credito = notas_credito.filtered(
                            lambda inv: inv.partner_id.l10n_latam_identification_type_id.name not in ['RUC']
                        )
            else:
                #dominio para facturas de cliente
                domain = [
                    ('invoice_date', '>=', record.fecha_desde), #solo facturas dentro del rango de fechas indicado
                    ('invoice_date', '<=', record.fecha_hasta),
                    ('move_type', '=', 'out_invoice'),  #solo facturas de cliente
                    ('state', '=', 'posted'),   #solo facturas posteadas
                    ('edi_state', '=', 'sent')  #solo facturas enviadas a sunat
                ]
                #dominio para notas de credito de cliente
                domain_notas_credito = [
                    ('invoice_date', '>=', record.fecha_desde),
                    ('invoice_date', '<=', record.fecha_hasta),
                    ('move_type', '=', 'out_refund'),  #solo notas de crédito de cliente
                    ('state', '=', 'posted'),
                    ('edi_state', '=', 'sent')
                ]
                #si se ingreso un cliente filtro las facturas y nc de acuerdo a ese cliente
                if record.cliente:
                    domain.append(('partner_id', '=', record.cliente.id))
                    domain_notas_credito.append(('partner_id', '=', record.cliente.id))
                #si se ingreso un vendedor filtro las facturas y nc de acuerdo a ese vendedor
                if record.usuario_vendedor:
                    domain.append(('invoice_user_id', '=', record.usuario_vendedor.id))
                    domain_notas_credito.append(('invoice_user_id', '=', record.usuario_vendedor.id))
                facturas = self.env['account.move'].search(domain)
                notas_credito = self.env['account.move'].search(domain_notas_credito)
                #si se ingreso un producto filtro las facturas y nc de acuerdo a ese producto
                if record.prod:
                    facturas_prod = facturas.filtered(lambda inv: any(line.product_id.id == record.prod.id for line in inv.line_ids))
                    facturas = facturas_prod
                    facturas_nc_prod = notas_credito.filtered(lambda inv: any(line.product_id.id == record.prod.id for line in inv.line_ids))
                    notas_credito = facturas_nc_prod
                #si se ingreso una marca filtro las facturas y nc de acuerdo a esa marca
                if record.marca_categoria:
                    facturas_marca = facturas.filtered(lambda factura: any(line.product_id.categ_id.id == record.marca_categoria.id for line in factura.line_ids))
                    facturas = facturas_marca
                    facturas_nc_marca = notas_credito.filtered(lambda factura: any(line.product_id.categ_id.id == record.marca_categoria.id for line in factura.line_ids))
                    notas_credito = facturas_nc_marca
            #me quedo solo con las notas de credito parciales
            notas_credito = notas_credito.filtered(
                lambda nc: nc.reversed_entry_id and nc.amount_total < nc.reversed_entry_id.amount_total
            )
            #excluyo a las facturas Revertidas, que quiere decir que tienen su monto total saldado por la nota de credito
            facturas = facturas.filtered(lambda factura: factura.payment_state != 'reversed')
            #combinar facturas y notas de crédito parciales
            totalidad_facturas = facturas | notas_credito
            #ordenar por fecha
            totalidad_facturas = totalidad_facturas.sorted(key=lambda factura: factura.invoice_date, reverse=True)

        return totalidad_facturas
    
    #ESTRUCTURA PARA TIPO VENDEDOR_MARCA
    def template_vendedor_marca(self, facturas, tipo, clientes, vendedores, marcas_unicas, productos):
        report_data = []    #este se devolvera y aqui estara toda la estructura lista para recorrer
        total_usd_reporte = 0.0 
        total_pen_reporte = 0.0  
        total_usd_reporte_impuestos = 0.0 
        total_pen_reporte_impuestos = 0.0 
        total_usd_reporte_valor_impuestos = 0.0  
        total_pen_reporte_valor_impuestos = 0.0 
        
        for vendedor in sorted(vendedores, key=lambda v: v.name.lower()):
            facturas_vendedor = facturas.filtered(lambda f: f.invoice_user_id == vendedor)
            marcas = facturas_vendedor.mapped('invoice_line_ids.product_id.categ_id')  

            marcas_data = []
            total_usd_vendedor = 0.0  
            total_pen_vendedor = 0.0  
            total_usd_vendedor_impuestos = 0.0  
            total_pen_vendedor_impuestos = 0.0  
            total_valor_impuestos_usd_vendedor = 0.0
            total_valor_impuestos_pen_vendedor = 0.0
            
            if self.marca_categoria:    #si hay una marca elegida solo recorro esa
                marcas = [self.marca_categoria]
            if self.prod:   #si hay un producto elegido solo pongo la marca correspondiente a ese producto
                marcas = marcas.filtered(
                    lambda marca: any(
                        line.product_id == self.prod and line.product_id.categ_id == marca
                        for factura in facturas_vendedor
                        for line in factura.invoice_line_ids
                    )
                )
            for marca in sorted(marcas, key=lambda m: m.name.lower()):
                facturas_marca = []
                total_usd = 0.0
                total_pen = 0.0
                total_usd_impuestos = 0.0
                total_pen_impuestos = 0.0
                total_valor_impuestos_usd = 0.0
                total_valor_impuestos_pen = 0.0

                for factura in facturas_vendedor:
                    lineas_marca = factura.invoice_line_ids.filtered(lambda l: l.product_id.categ_id == marca)
                    if self.prod:
                        lineas_marca = lineas_marca.filtered(lambda l: l.product_id == self.prod and l.product_id.categ_id == marca)
                    for linea in lineas_marca:
                        #total por monead
                        is_credit_note = factura.move_type == 'out_refund'
                        cantidad = -linea.quantity if is_credit_note else linea.quantity
                        total_dolar_fac = -linea.price_subtotal if is_credit_note and factura.currency_id.name == "USD" else linea.price_subtotal if factura.currency_id.name == "USD" else 0.0
                        total_pen_fac = -linea.price_subtotal if is_credit_note and factura.currency_id.name == "PEN" else linea.price_subtotal if factura.currency_id.name == "PEN" else 0.0
                        total_dolar_fac_impuestos = -linea.price_total if is_credit_note and factura.currency_id.name == "USD" else linea.price_total if factura.currency_id.name == "USD" else 0.0
                        total_pen_fac_impuestos = -linea.price_total if is_credit_note and factura.currency_id.name == "PEN" else linea.price_total if factura.currency_id.name == "PEN" else 0.0
                        valor_impuesto_dolar = total_dolar_fac_impuestos - total_dolar_fac
                        valor_impuesto_pen = total_pen_fac_impuestos - total_pen_fac

                        facturas_marca.append({
                            "factura": factura.name,
                            "fecha_creacion_factura": factura.invoice_date or factura.create_date,
                            "cliente": factura.partner_id.name,
                            "producto": linea.product_id.name,
                            "cantidad": cantidad,
                            "unidad": linea.product_uom_id.name,
                            "precio": linea.price_unit,
                            "total_dolar": total_dolar_fac,
                            "total_pen": total_pen_fac,
                            "total_dolar_impuestos": total_dolar_fac_impuestos,
                            "total_pen_impuestos": total_pen_fac_impuestos,
                            "valor_impuesto_dolar": valor_impuesto_dolar,
                            "valor_impuesto_pen": valor_impuesto_pen,
                            "moneda": factura.currency_id.name,
                            "impuestos": linea.tax_ids
                        })

                        #totales por marca
                        total_usd += total_dolar_fac
                        total_pen += total_pen_fac
                        total_usd_impuestos += total_dolar_fac_impuestos
                        total_pen_impuestos += total_pen_fac_impuestos
                        total_valor_impuestos_usd += valor_impuesto_dolar
                        total_valor_impuestos_pen += valor_impuesto_pen

                #las ordeno ascendentemente y las notas de credito van al ultimo
                notas_credito = [f for f in facturas_marca if f['cantidad'] < 0]
                facturas_normales = [f for f in facturas_marca if f['cantidad'] >= 0]
                notas_credito = sorted(notas_credito, key=lambda f: f['fecha_creacion_factura'])
                facturas_marca = sorted(facturas_normales, key=lambda f: f['fecha_creacion_factura']) + notas_credito

                #total por vendedor
                total_usd_vendedor += total_usd
                total_pen_vendedor += total_pen
                total_usd_vendedor_impuestos += total_usd_impuestos
                total_pen_vendedor_impuestos += total_pen_impuestos
                total_valor_impuestos_usd_vendedor += total_valor_impuestos_usd
                total_valor_impuestos_pen_vendedor += total_valor_impuestos_pen

                marcas_data.append({
                    "marca": marca.name,
                    "facturas": facturas_marca,
                    "total_usd": total_usd,
                    "total_pen": total_pen,
                    "total_usd_impuestos": total_usd_impuestos,
                    "total_pen_impuestos": total_pen_impuestos,
                    "total_valor_impuestos_usd": total_valor_impuestos_usd,
                    "total_valor_impuestos_pen": total_valor_impuestos_pen
                })

            report_data.append({
                "vendedor": vendedor.name,
                "marcas": marcas_data,
                "total_usd_vendedor": total_usd_vendedor,
                "total_pen_vendedor": total_pen_vendedor,
                "total_usd_vendedor_impuestos": total_usd_vendedor_impuestos,
                "total_pen_vendedor_impuestos": total_pen_vendedor_impuestos,
                "total_valor_impuestos_usd_vendedor": total_valor_impuestos_usd_vendedor,
                "total_valor_impuestos_pen_vendedor": total_valor_impuestos_pen_vendedor
            })

            #total por reporte
            total_usd_reporte += total_usd_vendedor
            total_pen_reporte += total_pen_vendedor
            total_usd_reporte_impuestos += total_usd_vendedor_impuestos
            total_pen_reporte_impuestos += total_pen_vendedor_impuestos
            total_usd_reporte_valor_impuestos += total_valor_impuestos_usd_vendedor
            total_pen_reporte_valor_impuestos += total_valor_impuestos_pen_vendedor
        
        return self.generate_pdf_report(facturas, tipo, clientes, vendedores, productos, marcas_unicas, report_data, total_usd_reporte, total_pen_reporte, total_usd_reporte_impuestos, total_pen_reporte_impuestos, total_usd_reporte_valor_impuestos, total_pen_reporte_valor_impuestos)
    
    #ESTRUCTURA PARA TIPO CLIENTE_PRODUCTO
    def template_cliente_producto(self, facturas, tipo, clientes, vendedores, marcas_unicas, productos):
        report_data = []    #este se devolvera y aqui estara toda la estructura lista para recorrer
        total_usd_reporte = 0.0 
        total_pen_reporte = 0.0  
        total_usd_reporte_impuestos = 0.0 
        total_pen_reporte_impuestos = 0.0 
        total_usd_reporte_valor_impuestos = 0.0  
        total_pen_reporte_valor_impuestos = 0.0

        for cliente in sorted(clientes, key=lambda c: c.name.lower()):  #ordeno los clientes alfabeticamente
            facturas_cliente = facturas.filtered(lambda f: f.partner_id == cliente)
            productos = facturas_cliente.mapped('invoice_line_ids.product_id')  
            
            productos_data = []
            total_usd_cliente = 0.0  
            total_pen_cliente = 0.0  
            total_usd_cliente_impuestos = 0.0  
            total_pen_cliente_impuestos = 0.0
            total_usd_cliente_valor_impuestos = 0.0  
            total_pen_cliente_valor_impuestos = 0.0
            
            if self.prod:    #si hay una producto solo recorro ese producto
                productos = [self.prod]
            for producto in sorted(productos, key=lambda p: p.name.lower()):    #ordeno los productos alfabeticamente
                facturas_producto = []
                total_usd = 0.0
                total_pen = 0.0
                total_usd_impuestos = 0.0
                total_pen_impuestos = 0.0
                total_usd_valor_impuestos = 0.0  
                total_pen_valor_impuestos = 0.0

                for factura in facturas_cliente:
                    lineas_producto = factura.invoice_line_ids.filtered(lambda l: l.product_id == producto)
                    for linea in lineas_producto:
                        #totales por moneda
                        is_credit_note = factura.move_type == "out_refund"
                        cantidad = -linea.quantity if is_credit_note else linea.quantity
                        total_dolar_fac = (linea.price_subtotal if factura.currency_id.name == "USD" else 0.0) * (-1 if is_credit_note else 1)
                        total_pen_fac = (linea.price_subtotal if factura.currency_id.name == "PEN" else 0.0) * (-1 if is_credit_note else 1)
                        total_dolar_fac_impuestos = (linea.price_total if factura.currency_id.name == "USD" else 0.0) * (-1 if is_credit_note else 1)
                        total_pen_fac_impuestos = (linea.price_total if factura.currency_id.name == "PEN" else 0.0) * (-1 if is_credit_note else 1)
                        valor_impuesto_dolar = ((linea.price_total - linea.price_subtotal) if factura.currency_id.name == "USD" else 0.0) * (-1 if is_credit_note else 1)
                        valor_impuesto_pen = ((linea.price_total - linea.price_subtotal) if factura.currency_id.name == "PEN" else 0.0) * (-1 if is_credit_note else 1)

                        facturas_producto.append({
                            "factura": factura.name,
                            "fecha_creacion_factura": factura.invoice_date or factura.create_date,
                            "cantidad": cantidad,
                            "unidad": linea.product_uom_id.name,
                            "descuento": linea.discount,
                            "precio": linea.price_unit,
                            "total_dolar": total_dolar_fac,
                            "total_pen": total_pen_fac,
                            "total_dolar_impuestos": total_dolar_fac_impuestos,
                            "total_pen_impuestos": total_pen_fac_impuestos,
                            "valor_impuesto_dolar": valor_impuesto_dolar,
                            "valor_impuesto_pen": valor_impuesto_pen,
                            "moneda": factura.currency_id.name,
                            "impuestos": linea.tax_ids,
                        })

                        #totales por producto
                        total_usd += total_dolar_fac
                        total_pen += total_pen_fac
                        total_usd_impuestos += total_dolar_fac_impuestos
                        total_pen_impuestos += total_pen_fac_impuestos
                        total_usd_valor_impuestos += valor_impuesto_dolar
                        total_pen_valor_impuestos += valor_impuesto_pen

                #las ordeno ascendentemente y las notas de credito van al ultimo
                notas_credito = [f for f in facturas_producto if f['cantidad'] < 0]
                facturas_normales = [f for f in facturas_producto if f['cantidad'] >= 0]
                notas_credito = sorted(notas_credito, key=lambda f: f['fecha_creacion_factura'])
                facturas_producto = sorted(facturas_normales, key=lambda f: f['fecha_creacion_factura']) + notas_credito

                #totales por cliente
                total_usd_cliente += total_usd
                total_pen_cliente += total_pen
                total_usd_cliente_impuestos += total_usd_impuestos
                total_pen_cliente_impuestos += total_pen_impuestos
                total_usd_cliente_valor_impuestos += total_usd_valor_impuestos  
                total_pen_cliente_valor_impuestos += total_pen_valor_impuestos

                productos_data.append({
                    "producto": producto.name,
                    "facturas": facturas_producto,
                    "total_usd": total_usd,
                    "total_pen": total_pen,
                    "total_usd_impuestos": total_usd_impuestos,
                    "total_pen_impuestos": total_pen_impuestos,
                    "total_usd_valor_impuestos": total_usd_valor_impuestos,
                    "total_pen_valor_impuestos": total_pen_valor_impuestos,
                })

            report_data.append({
                "cliente": cliente.name,
                "productos": productos_data,
                "total_usd_cliente": total_usd_cliente,
                "total_pen_cliente": total_pen_cliente,
                "total_usd_cliente_impuestos": total_usd_cliente_impuestos,
                "total_pen_cliente_impuestos": total_pen_cliente_impuestos,
                "total_usd_cliente_valor_impuestos": total_usd_cliente_valor_impuestos,
                "total_pen_cliente_valor_impuestos": total_pen_cliente_valor_impuestos
            })

            #totales por reporte
            total_usd_reporte += total_usd_cliente
            total_pen_reporte += total_pen_cliente
            total_usd_reporte_impuestos += total_usd_cliente_impuestos
            total_pen_reporte_impuestos += total_pen_cliente_impuestos
            total_usd_reporte_valor_impuestos += total_usd_cliente_valor_impuestos
            total_pen_reporte_valor_impuestos += total_pen_cliente_valor_impuestos
        
        return self.generate_pdf_report(facturas, tipo, clientes, vendedores, productos, marcas_unicas, report_data, total_usd_reporte, total_pen_reporte, total_usd_reporte_impuestos, total_pen_reporte_impuestos, total_usd_reporte_valor_impuestos, total_pen_reporte_valor_impuestos)
    
    #ESTRUCTURA PARA VENTAS CLIENTE
    def template_ventas_cliente(self, facturas, tipo, clientes, vendedores, marcas_unicas, productos):
        clientes = sorted(clientes, key=lambda c: c.name.lower())   #con esto obtengo los clientes ordenados alfabeticamente
        report_data = []    #este se devolvera y aqui estara toda la estructura lista para recorrer
        total_usd_reporte = 0.0 
        total_pen_reporte = 0.0  
        total_usd_reporte_impuestos = 0.0 
        total_pen_reporte_impuestos = 0.0 
        total_usd_reporte_valor_impuestos = 0.0  
        total_pen_reporte_valor_impuestos = 0.0 
        
        for cliente in clientes:
            facturas_cliente = facturas.filtered(lambda f: f.partner_id == cliente)
            
            facturas_data = []
            total_usd_cliente_sin_impuestos = 0.0  
            total_usd_cliente_valor_impuestos = 0.0  
            total_usd_cliente_con_impuestos = 0.0  
            total_pen_cliente_sin_impuestos = 0.0  
            total_pen_cliente_valor_impuestos = 0.0  
            total_pen_cliente_con_impuestos = 0.0  

            for factura in facturas_cliente:
                #totales por moneda
                is_credit_note = factura.move_type == "out_refund"
                total_dolar_fac = (factura.amount_untaxed if factura.currency_id.name == "USD" else 0.0) * (-1 if is_credit_note else 1)
                total_pen_fac = (factura.amount_untaxed if factura.currency_id.name == "PEN" else 0.0) * (-1 if is_credit_note else 1)
                total_dolar_fac_impuestos = (factura.amount_total if factura.currency_id.name == "USD" else 0.0) * (-1 if is_credit_note else 1)
                total_pen_fac_impuestos = (factura.amount_total if factura.currency_id.name == "PEN" else 0.0) * (-1 if is_credit_note else 1)
                valor_impuesto_dolar = (factura.amount_tax if factura.currency_id.name == "USD" else 0.0) * (-1 if is_credit_note else 1)
                valor_impuesto_pen = (factura.amount_tax if factura.currency_id.name == "PEN" else 0.0) * (-1 if is_credit_note else 1)
                
                if tipo == "Detallado":
                    #valor del estado de la factura dependiendo de su pago o del pago de letras si es que tiene
                    estado = ""
                    if factura.letter_id:
                        #si hay canje recorro las letras que tiene
                        letter_states = [line.state for line in factura.letter_id.letter_line_ids]
                        
                        if all(state == "paid" for state in letter_states):
                            estado = "CANCELADO"
                        elif any(state == "paid" for state in letter_states):
                            estado = "PARCIAL"
                        else:
                            estado = "DEBE"
                    else:
                        if factura.payment_state == "not_paid":
                            estado = "DEBE"
                        elif factura.payment_state == "partial":
                            estado = "PARCIAL"
                        elif factura.payment_state in ["paid", "in_payment"]:
                            estado = "CANCELADO"
                    
                    facturas_data.append({
                        "fecha_creacion_factura": factura.invoice_date,
                        "factura": factura.name,
                        "fecha_vencimiento_factura": factura.invoice_date_due,
                        "vendedor": factura.invoice_user_id.partner_id.name,
                        "estado": estado,
                        "total_dolar_sin_impuesto": total_dolar_fac,
                        "total_pen_sin_impuesto": total_pen_fac,
                        "total_dolar_con_impuestos": total_dolar_fac_impuestos,
                        "total_pen_con_impuestos": total_pen_fac_impuestos,
                        "valor_impuesto_dolar": valor_impuesto_dolar,
                        "valor_impuesto_pen": valor_impuesto_pen,
                        "moneda": factura.currency_id.name,
                        "is_credit_note": is_credit_note
                    })
                
                #totales por cliente
                total_usd_cliente_sin_impuestos += total_dolar_fac
                total_usd_cliente_valor_impuestos += valor_impuesto_dolar
                total_usd_cliente_con_impuestos += total_dolar_fac_impuestos
                total_pen_cliente_sin_impuestos += total_pen_fac
                total_pen_cliente_valor_impuestos += valor_impuesto_pen
                total_pen_cliente_con_impuestos += total_pen_fac_impuestos
                
            #ordeno ascendentemente las facturas y las notas de credito van al ultimo
            notas_credito = [f for f in facturas_data if f['is_credit_note'] == True]
            facturas_normales = [f for f in facturas_data if f['is_credit_note'] == False]
            notas_credito = sorted(notas_credito, key=lambda f: f['fecha_creacion_factura'])
            facturas_data = sorted(facturas_normales, key=lambda f: f['fecha_creacion_factura']) + notas_credito
            
            data = {
                "cliente": cliente.name,
                "total_usd_cliente_sin_impuestos": total_usd_cliente_sin_impuestos,
                "total_usd_cliente_valor_impuestos": total_usd_cliente_valor_impuestos,
                "total_usd_cliente_con_impuestos": total_usd_cliente_con_impuestos,
                "total_pen_cliente_sin_impuestos": total_pen_cliente_sin_impuestos,
                "total_pen_cliente_valor_impuestos": total_pen_cliente_valor_impuestos,
                "total_pen_cliente_con_impuestos": total_pen_cliente_con_impuestos
            }

            #solo le agrego las facturas si es detallado, ya que la estructura es similar para el general solo que sin las facturas
            if tipo == "Detallado":
                data["facturas"] = facturas_data
            
            report_data.append(data)
            
            #total del reporte
            total_usd_reporte += total_usd_cliente_sin_impuestos
            total_pen_reporte += total_pen_cliente_sin_impuestos
            total_usd_reporte_impuestos += total_usd_cliente_con_impuestos
            total_pen_reporte_impuestos += total_pen_cliente_con_impuestos
            total_usd_reporte_valor_impuestos += total_usd_cliente_valor_impuestos  
            total_pen_reporte_valor_impuestos += total_pen_cliente_valor_impuestos 
        return self.generate_pdf_report(facturas, tipo, clientes, vendedores, productos, marcas_unicas, report_data, total_usd_reporte, total_pen_reporte, total_usd_reporte_impuestos, total_pen_reporte_impuestos, total_usd_reporte_valor_impuestos, total_pen_reporte_valor_impuestos)

    #ESTRUCTURA PARA VENTAS VENDEDOR INICIAL 
    def template_ventas_vendedor(self, facturas, tipo, clientes, vendedores, marcas_unicas, productos):
        report_data = []    #este se devolvera y aqui estara toda la estructura lista para recorrer
        total_usd_reporte = 0.0 
        total_pen_reporte = 0.0  
        total_usd_reporte_impuestos = 0.0 
        total_pen_reporte_impuestos = 0.0 
        total_usd_reporte_valor_impuestos = 0.0  
        total_pen_reporte_valor_impuestos = 0.0 
        
        for vendedor in sorted(vendedores, key=lambda v: v.name.lower()):  #ordeno por nombre de a-z
            facturas_vendedor = facturas.filtered(lambda f: f.invoice_user_id == vendedor)

            total_usd_vendedor_sin_impuestos = 0.0
            total_pen_vendedor_sin_impuestos = 0.0
            total_usd_vendedor_con_impuestos = 0.0
            total_pen_vendedor_con_impuestos = 0.0
            total_usd_vendedor_valor_impuestos = 0.0
            total_pen_vendedor_valor_impuestos = 0.0

            #diccionario para guardar los terminos de pago
            terminos_pago_dict = {}

            for factura in facturas_vendedor:
                #nombre del termino de pago dependiendo de las fechas de la factura
                if factura.invoice_date_due and factura.invoice_date:
                    dias = (factura.invoice_date_due - factura.invoice_date).days
                    if factura.letter_id:
                        if dias == 0:
                            termino_pago = "Contado Letra(s)"
                        else:
                            termino_pago = f"Letra(s) {dias} Día(s)"
                    else:
                        if dias == 0:
                            termino_pago = "Contado"
                        else:
                            termino_pago = f"{dias} Día(s)"
                else:
                    termino_pago = "Sin término definido"
                
                is_credit_note = factura.move_type == "out_refund"
                total_dolar_fac = (factura.amount_untaxed if factura.currency_id.name == "USD" else 0.0) * (-1 if is_credit_note else 1)
                total_pen_fac = (factura.amount_untaxed if factura.currency_id.name == "PEN" else 0.0) * (-1 if is_credit_note else 1)
                total_dolar_fac_impuestos = (factura.amount_total if factura.currency_id.name == "USD" else 0.0) * (-1 if is_credit_note else 1)
                total_pen_fac_impuestos = (factura.amount_total if factura.currency_id.name == "PEN" else 0.0) * (-1 if is_credit_note else 1)
                valor_impuesto_dolar = (factura.amount_tax if factura.currency_id.name == "USD" else 0.0) * (-1 if is_credit_note else 1)
                valor_impuesto_pen = (factura.amount_tax if factura.currency_id.name == "PEN" else 0.0) * (-1 if is_credit_note else 1)
                #evalucaion de estados segun letras y estados del pago de factura
                estado = ""
                if factura.letter_id:
                    #si hay canje recorro las letras que tiene
                    letter_states = [line.state for line in factura.letter_id.letter_line_ids]
                    
                    if all(state == "paid" for state in letter_states):
                        estado = "CANCELADO"
                    elif any(state == "paid" for state in letter_states):
                        estado = "PARCIAL"
                    else:
                        estado = "DEBE"
                else:
                    if factura.payment_state == "not_paid":
                        estado = "DEBE"
                    elif factura.payment_state == "partial":
                        estado = "PARCIAL"
                    elif factura.payment_state in ["paid", "in_payment"]:
                        estado = "CANCELADO"
                #solo se agregan los terminos de pago que no existen
                if termino_pago not in terminos_pago_dict:
                    terminos_pago_dict[termino_pago] = {
                        "nombre_principal_termino_pago": "Contado" if "Contado" in termino_pago else "Crédito",  
                        "nombre_secundario_termino_pago": termino_pago.replace("Contado", "").strip() if "Contado" in termino_pago else termino_pago,
                        "facturas": [],
                        "total_usd_termino_sin_impuestos": 0.0,
                        "total_pen_termino_sin_impuestos": 0.0,
                        "total_usd_termino_con_impuestos": 0.0,
                        "total_pen_termino_con_impuestos": 0.0,
                        "valor_usd_impuestos": 0.0,
                        "valor_pen_impuestos": 0.0,
                    }
                #creacion de la estructura de la factura para el termino de pago
                terminos_pago_dict[termino_pago]["facturas"].append({
                    "cliente": factura.partner_id.name,
                    "fecha_creacion_factura": factura.invoice_date,
                    "factura": factura.name,
                    "fecha_vencimiento_factura": factura.invoice_date_due,
                    "estado": estado,
                    "total_dolar_sin_impuesto": total_dolar_fac,
                    "total_pen_sin_impuesto": total_pen_fac,
                    "total_dolar_con_impuestos": total_dolar_fac_impuestos,
                    "total_pen_con_impuestos": total_pen_fac_impuestos,
                    "valor_impuesto_dolar": valor_impuesto_dolar,
                    "valor_impuesto_pen": valor_impuesto_pen,
                    "moneda": factura.currency_id.name,
                    "is_credit_note": is_credit_note,
                })
                #totales de cada termino de pago
                terminos_pago_dict[termino_pago]["total_usd_termino_sin_impuestos"] += total_dolar_fac
                terminos_pago_dict[termino_pago]["total_pen_termino_sin_impuestos"] += total_pen_fac
                terminos_pago_dict[termino_pago]["total_usd_termino_con_impuestos"] += total_dolar_fac_impuestos
                terminos_pago_dict[termino_pago]["total_pen_termino_con_impuestos"] += total_pen_fac_impuestos
                terminos_pago_dict[termino_pago]["valor_usd_impuestos"] += valor_impuesto_dolar
                terminos_pago_dict[termino_pago]["valor_pen_impuestos"] += valor_impuesto_pen
                #totales de cada vendedor
                total_usd_vendedor_sin_impuestos += total_dolar_fac
                total_pen_vendedor_sin_impuestos += total_pen_fac
                total_usd_vendedor_con_impuestos += total_dolar_fac_impuestos
                total_pen_vendedor_con_impuestos += total_pen_fac_impuestos
                total_usd_vendedor_valor_impuestos += valor_impuesto_dolar
                total_pen_vendedor_valor_impuestos += valor_impuesto_pen
            #ordeno los terminos de pago, contado siempre primero y despues los de credito segun su dia ascendente
            terminos_pago_data = sorted(terminos_pago_dict.values(), key=lambda t: (
                0 if t["nombre_principal_termino_pago"] == "Contado" else 1,  
                0 if t["nombre_principal_termino_pago"] == "Contado" and not t["nombre_secundario_termino_pago"] else 1,  #contado sin nombre secundario va primero siempre
                int(t["nombre_secundario_termino_pago"].split()[0]) if t["nombre_principal_termino_pago"] == "Crédito" and t["nombre_secundario_termino_pago"].split()[0].isdigit() else float('inf')
            ))
            #le agrego a report data los vendedores con su estructura
            report_data.append({
                "vendedor": vendedor.name,
                "terminos_de_pago": terminos_pago_data,
                "total_usd_vendedor_sin_impuestos": total_usd_vendedor_sin_impuestos,
                "total_pen_vendedor_sin_impuestos": total_pen_vendedor_sin_impuestos,
                "total_usd_vendedor_con_impuestos": total_usd_vendedor_con_impuestos,
                "total_pen_vendedor_con_impuestos": total_pen_vendedor_con_impuestos,
                "total_usd_vendedor_valor_impuestos": total_usd_vendedor_valor_impuestos,
                "total_pen_vendedor_valor_impuestos": total_pen_vendedor_valor_impuestos,
            })
            #ordenar facturas por fecha y notas de credito
            for termino_pago, data in terminos_pago_dict.items():
                data["facturas"] = sorted(
                    data["facturas"],
                    key=lambda f: (
                        1 if f["is_credit_note"] else 0,  #notas de credito al final
                        f["fecha_creacion_factura"] or float('inf')  #y ordeno por fecha
                    )
                )
        #hago la sumatoria de los totales de los vendedores para el reporte total
        for vendedor_data in report_data:
            total_usd_reporte += vendedor_data["total_usd_vendedor_sin_impuestos"]
            total_pen_reporte += vendedor_data["total_pen_vendedor_sin_impuestos"]
            total_usd_reporte_impuestos += vendedor_data["total_usd_vendedor_con_impuestos"]
            total_pen_reporte_impuestos += vendedor_data["total_pen_vendedor_con_impuestos"]
            total_usd_reporte_valor_impuestos += vendedor_data["total_usd_vendedor_valor_impuestos"]
            total_pen_reporte_valor_impuestos += vendedor_data["total_pen_vendedor_valor_impuestos"]
        
        return self.generate_pdf_report(facturas, tipo, clientes, vendedores, productos, marcas_unicas, report_data, total_usd_reporte, total_pen_reporte, total_usd_reporte_impuestos, total_pen_reporte_impuestos, total_usd_reporte_valor_impuestos, total_pen_reporte_valor_impuestos)

    #ESTRUCTURA PARA COMPRAS
    def template_compras(self, facturas, tipo, clientes, vendedores, marcas_unicas, productos):
        report_data = []    #este se devolvera y aqui estara toda la estructura lista para recorrer
        total_usd_reporte = 0.0 
        total_pen_reporte = 0.0  
        total_usd_reporte_impuestos = 0.0 
        total_pen_reporte_impuestos = 0.0 
        total_usd_reporte_valor_impuestos = 0.0  
        total_pen_reporte_valor_impuestos = 0.0 
        
        for cliente in clientes:
            facturas_cliente = facturas.filtered(lambda f: f.partner_id == cliente) #solo facturas de este proveedor que recorro
            
            facturas_data = []  #aca se almacena la data de cada linea de cada factura
            total_usd_cliente = 0.0 
            total_pen_cliente = 0.0  
            total_usd_cliente_impuestos = 0.0 
            total_pen_cliente_impuestos = 0.0 
            total_usd_cliente_valor_impuestos = 0.0  
            total_pen_cliente_valor_impuestos = 0.0 
            
            for factura in facturas_cliente:
                lineas_factura = factura.invoice_line_ids
                for linea in lineas_factura:
                    
                    is_credit_note = factura.move_type == 'in_refund'
                    cantidad = -linea.quantity if is_credit_note else linea.quantity
                    total_dolar_fac = -linea.price_subtotal if is_credit_note and factura.currency_id.name == "USD" else linea.price_subtotal if factura.currency_id.name == "USD" else 0.0
                    total_pen_fac = -linea.price_subtotal if is_credit_note and factura.currency_id.name == "PEN" else linea.price_subtotal if factura.currency_id.name == "PEN" else 0.0
                    total_dolar_fac_impuestos = -linea.price_total if is_credit_note and factura.currency_id.name == "USD" else linea.price_total if factura.currency_id.name == "USD" else 0.0
                    total_pen_fac_impuestos = -linea.price_total if is_credit_note and factura.currency_id.name == "PEN" else linea.price_total if factura.currency_id.name == "PEN" else 0.0
                    valor_impuesto_dolar = total_dolar_fac_impuestos - total_dolar_fac
                    valor_impuesto_pen = total_pen_fac_impuestos - total_pen_fac
                    
                    facturas_data.append({
                        "factura": factura.name,
                        "fecha_creacion_factura": factura.invoice_date or factura.create_date,
                        "proveedor": factura.partner_id.name,
                        "producto": linea.product_id.name,
                        "cantidad": cantidad,
                        "unidad": linea.product_uom_id.name,
                        "precio": linea.price_unit,
                        "moneda": factura.currency_id.name,
                        "total_dolar": total_dolar_fac,
                        "total_pen": total_pen_fac,
                        "total_dolar_impuestos": total_dolar_fac_impuestos,
                        "total_pen_impuestos": total_pen_fac_impuestos,
                        "valor_impuesto_dolar": valor_impuesto_dolar,
                        "valor_impuesto_pen": valor_impuesto_pen,
                    })
                    
                    #totales por cliente proveedor
                    total_usd_cliente += total_dolar_fac
                    total_pen_cliente += total_pen_fac
                    total_usd_cliente_impuestos += total_dolar_fac_impuestos
                    total_pen_cliente_impuestos += total_pen_fac_impuestos
                    total_usd_cliente_valor_impuestos += valor_impuesto_dolar
                    total_pen_cliente_valor_impuestos += valor_impuesto_pen
                    
            
            notas_credito = [f for f in facturas_data if f['cantidad'] < 0]
            facturas_normales = [f for f in facturas_data if f['cantidad'] >= 0]
            notas_credito = sorted(notas_credito, key=lambda f: f['fecha_creacion_factura'])
            facturas_data = sorted(facturas_normales, key=lambda f: f['fecha_creacion_factura']) + notas_credito
            
            report_data.append({
                "proveedor": cliente.name,
                "facturas": facturas_data,
                "total_usd_cliente": total_usd_cliente,
                "total_pen_cliente": total_pen_cliente,
                "total_usd_cliente_impuestos": total_usd_cliente_impuestos,
                "total_pen_cliente_impuestos": total_pen_cliente_impuestos,
                "total_usd_cliente_valor_impuestos": total_usd_cliente_valor_impuestos,
                "total_pen_cliente_valor_impuestos": total_pen_cliente_valor_impuestos
            })

            #total por reporte
            total_usd_reporte += total_usd_cliente
            total_pen_reporte += total_pen_cliente
            total_usd_reporte_impuestos += total_usd_cliente_impuestos
            total_pen_reporte_impuestos += total_pen_cliente_impuestos
            total_usd_reporte_valor_impuestos += total_usd_cliente_valor_impuestos
            total_pen_reporte_valor_impuestos += total_pen_cliente_valor_impuestos
        
        return self.generate_pdf_report(facturas, tipo, clientes, vendedores, productos, marcas_unicas, report_data, total_usd_reporte, total_pen_reporte, total_usd_reporte_impuestos, total_pen_reporte_impuestos, total_usd_reporte_valor_impuestos, total_pen_reporte_valor_impuestos)
    
    #ESTRUCTURA PARA RANKING DE PRODUCTOS
    def template_ranking_productos(self, facturas, tipo, clientes, vendedores, marcas_unicas, productos):
        report_data = []    #este se devolvera y aqui estara toda la estructura lista para recorrer
        total_usd_reporte = 0.0 
        total_pen_reporte = 0.0  
        total_usd_reporte_impuestos = 0.0 
        total_pen_reporte_impuestos = 0.0 
        total_usd_reporte_valor_impuestos = 0.0  
        total_pen_reporte_valor_impuestos = 0.0 
        #uso un diccionario ya que si se repiten productos en facturas es mas facil manejarlo de este modo para que no se repitan y hacer las sumas
        productos_ranking = {}

        for factura in facturas:
            for linea in factura.invoice_line_ids:
                product_key = linea.product_id.id  #uso el id del producto como clave
                is_credit_note = factura.move_type == "out_refund"
                cantidad = -linea.quantity if is_credit_note else linea.quantity
                total_dolar_fac = (linea.price_subtotal if factura.currency_id.name == "USD" else 0.0) * (-1 if is_credit_note else 1)
                total_pen_fac = (linea.price_subtotal if factura.currency_id.name == "PEN" else 0.0) * (-1 if is_credit_note else 1)
                total_dolar_fac_impuestos = (linea.price_total if factura.currency_id.name == "USD" else 0.0) * (-1 if is_credit_note else 1)
                total_pen_fac_impuestos = (linea.price_total if factura.currency_id.name == "PEN" else 0.0) * (-1 if is_credit_note else 1)
                valor_impuesto_dolar = ((linea.price_total - linea.price_subtotal) if factura.currency_id.name == "USD" else 0.0) * (-1 if is_credit_note else 1)
                valor_impuesto_pen = ((linea.price_total - linea.price_subtotal) if factura.currency_id.name == "PEN" else 0.0) * (-1 if is_credit_note else 1)
                
                if product_key not in productos_ranking:    #aca valido si esa clave no esta en el diccionario significa que es un nuevo producto para ese proveedor y lo agrego
                    productos_ranking[product_key] = {  #esto es basicamente un diccionario unico que contiene dentro un diccionario de un solo producto, por eso a la key le pongo el id del producto
                        "codigo": linea.product_id.default_code,
                        "producto": linea.product_id.name,
                        "marca": linea.product_id.categ_id.name,
                        "cantidad": cantidad,
                        "total_dolar": total_dolar_fac,
                        "total_pen": total_pen_fac,
                        "total_dolar_con_impuestos": total_dolar_fac_impuestos,
                        "total_pen_con_impuestos": total_pen_fac_impuestos,
                        "valor_impuesto_dolar": valor_impuesto_dolar,
                        "valor_impuesto_pen": valor_impuesto_pen,
                        "moneda": factura.currency_id.name,
                    }
                else:
                    #y si ese producto ya existe, osea si su id ya esta en un diccionario, le sumo los valores de cantidad y totales al que ya existe
                    productos_ranking[product_key]["cantidad"] += cantidad
                    productos_ranking[product_key]["total_dolar"] += total_dolar_fac
                    productos_ranking[product_key]["total_pen"] += total_pen_fac
                    productos_ranking[product_key]["total_dolar_con_impuestos"] += total_dolar_fac_impuestos
                    productos_ranking[product_key]["total_pen_con_impuestos"] += total_pen_fac_impuestos
                    productos_ranking[product_key]["valor_impuesto_dolar"] += valor_impuesto_dolar
                    productos_ranking[product_key]["valor_impuesto_pen"] += valor_impuesto_pen
                    
                #totales del reporte
                total_usd_reporte += total_dolar_fac
                total_pen_reporte += total_pen_fac  
                total_usd_reporte_impuestos += total_dolar_fac_impuestos 
                total_pen_reporte_impuestos += total_pen_fac_impuestos 
                total_usd_reporte_valor_impuestos += valor_impuesto_dolar  
                total_pen_reporte_valor_impuestos += valor_impuesto_pen
        
        #ordeno la lista de los productos segun su cantidad y lo agrego a la estructura
        productos_ranking = sorted(productos_ranking.values(), key=lambda x: x["cantidad"], reverse=True)
        report_data.append(productos_ranking)
        
        return self.generate_pdf_report(facturas, tipo, clientes, vendedores, productos, marcas_unicas, report_data, total_usd_reporte, total_pen_reporte, total_usd_reporte_impuestos, total_pen_reporte_impuestos, total_usd_reporte_valor_impuestos, total_pen_reporte_valor_impuestos)

    def export_report(self):
        tipo = self.env.context.get('tipo', 'General')
        clientes = []
        vendedores = []
        marcas_unicas = []
        productos = []
        facturas = None
        for record in self:
            if record.tipo_reporte == 'vendedor_marca' or record.tipo_reporte == 'cliente_producto' or record.tipo_reporte == 'ventas_vendedor' or record.tipo_reporte == 'ventas_cliente' or record.tipo_reporte == 'compras' or record.tipo_reporte == 'ranking_productos' and record.fecha_desde and record.fecha_hasta:
                facturas = self.facturas_vendedor_marca_cliente_producto()
                if facturas:
                    for factura in facturas:
                        #guardo los clientes unicos
                        if factura.partner_id and factura.partner_id not in clientes:
                            clientes.append(factura.partner_id)
                        #guardo los vendedores unicos
                        if factura.invoice_user_id and factura.invoice_user_id not in vendedores:
                            vendedores.append(factura.invoice_user_id)
                        #guardo los productos unicos y marcas unicos
                        for line in factura.line_ids:
                            if line.product_id and line.product_id not in productos:
                                productos.append(line.product_id)
                            if line.product_id.categ_id and line.product_id.categ_id not in marcas_unicas:
                                marcas_unicas.append(line.product_id.categ_id)
                    
                    if record.tipo_reporte == 'vendedor_marca':
                        return self.template_vendedor_marca(facturas, tipo, clientes, vendedores, marcas_unicas, productos)
                    if record.tipo_reporte == 'cliente_producto':
                        return self.template_cliente_producto(facturas, tipo, clientes, vendedores, marcas_unicas, productos)
                    if record.tipo_reporte == 'ventas_cliente':
                        return self.template_ventas_cliente(facturas, tipo, clientes, vendedores, marcas_unicas, productos)
                    if record.tipo_reporte == 'ventas_vendedor':
                        return self.template_ventas_vendedor(facturas, tipo, clientes, vendedores, marcas_unicas, productos)
                    if record.tipo_reporte == 'compras':
                        return self.template_compras(facturas, tipo, clientes, vendedores, marcas_unicas, productos)
                    if record.tipo_reporte == 'ranking_productos':
                        return self.template_ranking_productos(facturas, tipo, clientes, vendedores, marcas_unicas, productos)
                else:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Búsqueda sin resultados',
                            'message': 'No se encontraron facturas para los filtros seleccionados.',
                            'sticky': False,
                        },
                    }