/** @odoo-module */

import { KanbanController } from "@web/views/kanban/kanban_controller";
import { registry } from '@web/core/registry';
import { kanbanView } from '@web/views/kanban/kanban_view';
export class ProjectKanbanController extends KanbanController {
   setup() {
       super.setup();
   }
   OnClickOpen() {
      const projectId = this.props.context.active_id;

      this.actionService.doAction({
          type: 'ir.actions.act_window',
          res_model: 'project.generate.task',
          name:'Generar Tareas',
          view_mode: 'form',
          view_type: 'form',
          views: [[false, 'form']],
          target: 'new',
          res_id: false,
          context: {
            default_project_id: projectId
        }
      });
   }
}
registry.category("views").add("button_in_kanban", {
   ...kanbanView,
   Controller: ProjectKanbanController,
   buttonTemplate: "button_task_kanban.KanbanView.Buttons",
});
