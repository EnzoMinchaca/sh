/** @odoo-module */

import { ListController } from "@web/views/list/list_controller";
import { useService } from "@web/core/utils/hooks";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
export class AccountPaidPDFListController extends ListController {
   setup() {
       super.setup();
       this.orm = useService("orm");
   }
   async OnClickOpenPDF() {
    try {
        // Obtener el dominio actual aplicado en la vista (filtros, búsqueda, etc.)
        const domain = this.props.domain || [];

        const records = await this.orm.call(
            'account.followup.paid',
            'search_read',
            [domain, ['id']],
        );

        // Obtener la agrupación desde el contexto
        const groupBy = this.props.groupBy || [];

        // Codificar cada valor del array groupBy
        const encodedGroupBy = groupBy.map(item => encodeURIComponent(item)).join(',');

        // Redirigir a la URL para descargar el reporte XLSX
        const ids = records.map(record => record.id).join(',');
        const url = `/account_paid/report?ids=${ids}&group_by=${encodedGroupBy}`;

        // Abrir la descarga en una nueva pestaña
        window.open(url, '_blank');

    } catch (error) {
        console.error("Error al obtener los registros:", error);
    }
 }
    async OnClickOpenXLSX() {
        try {
            const domain = this.props.domain || [];

            const records = await this.orm.call(
                'account.followup.paid',
                'search_read',
                [domain, ['id']],
            );

            // Obtener la agrupación desde el contexto
            const groupBy = this.props.groupBy || [];

            // Codificar cada valor del array groupBy
            const encodedGroupBy = groupBy.map(item => encodeURIComponent(item)).join(',');

            // Redirigir a la URL para descargar el reporte XLSX
            const ids = records.map(record => record.id).join(',');
            const url = `/move_line/export_xlsx?ids=${ids}&group_by=${encodedGroupBy}`;

            // Abrir la descarga en una nueva pestaña
            window.open(url, '_blank');
        } catch (error) {
            console.error("Error al obtener los registros para XLSX:", error);
        }
    }
}
registry.category("views").add("button_pdf_tree", {
   ...listView,
   Controller: AccountPaidPDFListController,
   buttonTemplate: "button_pdf_tree.ListView.Buttons",
});
