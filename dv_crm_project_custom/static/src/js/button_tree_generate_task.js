/** @odoo-module */

import { ListController } from "@web/views/list/list_controller";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
export class ProjectListController extends ListController {
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
registry.category("views").add("button_in_tree", {
   ...listView,
   Controller: ProjectListController,
   buttonTemplate: "button_task_tree.ListView.Buttons",
});
