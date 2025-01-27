/** @odoo-module **/

import {ProductTemplateAttributeLine} from "@sale_product_configurator/js/product_template_attribute_line/product_template_attribute_line";
import { patch } from "@web/core/utils/patch";


patch(ProductTemplateAttributeLine.prototype, {
    static: {
        props: {
            attribute_values: {
                type: Array,
                element: {
                    type: Object,
                    shape: Object.assign(
                        ProductTemplateAttributeLine.props.attribute_values.element.shape,
                        {
                            res_product_name: { type: [String, Boolean], optional: true },
                        }
                    ),
                },
            },
        },
    },
});