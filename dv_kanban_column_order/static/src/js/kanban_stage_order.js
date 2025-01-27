/** @odoo-module **/

import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { patch } from "@web/core/utils/patch";

patch(KanbanRenderer.prototype, {
    getGroupsOrRecords() {
        const { list } = this.props;
        if (list.isGrouped) {
            //Aplica solo a crm.lead
            if (this.props.list.config.resModel === 'crm.lead') {
                // Aplica una ordenación personalizada en el grupo "Solicitudes"
                list.groups.forEach(group => {
                    const { order_asc, order_desc, field_by_order_name } = group.list.records[0]?.data || {};
        
                    // Verificar si hay un campo de ordenamiento definido
                    if (field_by_order_name) {
                        const fieldName = field_by_order_name;  // Obtén el nombre del campo a ordenar
        
                        // Configura el orden según el campo `order_asc` o `order_desc`
                        group.list.records.sort((a, b) => {
                            const dateA = a.data[fieldName] ? new Date(a.data[fieldName]) : null;
                            const dateB = b.data[fieldName] ? new Date(b.data[fieldName]) : null;
        
                            if (dateA && dateB) {
                                return order_asc ? dateA - dateB : dateB - dateA;
                            }
                            return 0;
                        });
                    }
                });
            }
            return [...list.groups]
                .sort((a, b) => (a.value && !b.value ? 1 : !a.value && b.value ? -1 : 0))
                .map((group, i) => ({
                    group,
                    key: group.value === null ? `group_key_${i}` : String(group.value),
                }));
        } else {
            return list.records.map((record) => ({ record, key: record.id }));
        }
    }
});