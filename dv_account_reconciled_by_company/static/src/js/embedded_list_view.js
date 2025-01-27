 /** @odoo-module **/

import { BankRecWidgetFormEmbeddedListModel } from "@account_accountant/components/bank_reconciliation/embedded_list_view";
import { registry } from '@web/core/registry';

export class CustomBankRecWidgetFormEmbeddedListModel extends BankRecWidgetFormEmbeddedListModel {
    /* async load(params = {}) {

        // Extraer los valores de company_id desde el dominio
        const companyDomain = params.domain.find(item => item[0] === 'company_id' && item[1] === 'in');
        if (companyDomain) {
            const companyIds = companyDomain[2]; // Obtener el array de IDs de compañía
            params.context.allowed_company_ids = companyIds; // Asignar estos IDs a allowed_company_ids
        }

        // Llamar al método original usando `super`
        return super.load(params);
    } */
}

// Registrar la nueva clase
registry.category('views').add('BankRecWidgetFormEmbeddedListModel', CustomBankRecWidgetFormEmbeddedListModel);