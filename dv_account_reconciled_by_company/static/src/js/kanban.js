//test para agregar los apuntes de las compañias externas
export class BankRecKanbanRecord extends KanbanRecord {
    notebookAmlsListViewProps(){
        const initParams = this.state.bankRecEmbeddedViewsData.amls;
        const ctx = initParams.context;
        const suspenseLine = this.state.bankRecRecordData.line_ids.records.filter((l) => l.data.flag == "auto_balance");
        if (suspenseLine.length) {
            // Change the sort order of the AML's in the list view based on the amount of the suspense line
            // This is done from JS instead of python because the embedded_views_data is only prepared when selecting
            // a statement line, and not after mounting an AML that would change the auto_balance value (suspense line)
            ctx['preferred_aml_value'] = suspenseLine[0].data.amount_currency * -1;
            ctx['preferred_aml_currency_id'] = suspenseLine[0].data.currency_id[0];
        }
        return {
            type: "list",
            noBreadcrumbs: true,
            resModel: "account.move.line",
            searchMenuTypes: ["filter"],
            domain: initParams.domain,
            dynamicFilters: initParams.dynamic_filters,
            context: ctx,
            allowSelectors: false,
            searchViewId: false, // little hack: force to load the search view info
            globalState: initParams.exportState,
        }
    }
}