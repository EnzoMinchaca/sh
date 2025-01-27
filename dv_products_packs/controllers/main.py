from odoo.addons.sale_product_configurator.controllers.main import ProductConfiguratorController
from odoo.http import request
from datetime import datetime

class CustomProductConfiguratorController(ProductConfiguratorController):
    def _get_product_information(
        self,
        product_template,
        combination,
        currency_id,
        so_date,
        quantity=1,
        product_uom_id=None,
        pricelist_id=None,
        parent_combination=None,
    ):
        pricelist = request.env['product.pricelist'].browse(pricelist_id)
        product_uom = request.env['uom.uom'].browse(product_uom_id)
        currency = request.env['res.currency'].browse(currency_id)
        product = product_template._get_variant_for_combination(combination)
        attribute_exclusions = product_template._get_attribute_exclusions(
            parent_combination=parent_combination,
            combination_ids=combination.ids,
        )

        return dict(
            product_tmpl_id=product_template.id,
            **self._get_basic_product_information(
                product or product_template,
                pricelist,
                combination,
                quantity=quantity,
                uom=product_uom,
                currency=currency,
                date=datetime.fromisoformat(so_date),
            ),
            quantity=quantity,
            attribute_lines=[dict(
                id=ptal.id,
                attribute=dict(**ptal.attribute_id.read(['id', 'name', 'display_type'])[0]),
                attribute_values=[
                    dict(
                        #Agrega el campo res_product_name
                        **ptav.read(['name', 'res_product_name', 'html_color', 'image', 'is_custom'])[0],
                        price_extra=ptav.currency_id._convert(
                            ptav.price_extra,
                            currency,
                            request.env.company,
                            datetime.fromisoformat(so_date).date(),
                        ),
                    ) for ptav in ptal.product_template_value_ids
                    if ptav.ptav_active or combination and ptav.id in combination.ids
                ],
                selected_attribute_value_ids=combination.filtered(
                    lambda c: ptal in c.attribute_line_id
                ).ids,
                create_variant=ptal.attribute_id.create_variant,
            ) for ptal in product_template.attribute_line_ids],
            exclusions=attribute_exclusions['exclusions'],
            archived_combinations=attribute_exclusions['archived_combinations'],
            parent_exclusions=attribute_exclusions['parent_exclusions'],
        )