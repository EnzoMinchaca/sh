from odoo import models, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def _timesheet_create_project_prepare_values(self):
        values = super(SaleOrderLine, self)._timesheet_create_project_prepare_values()
        project_manager_id = self.order_id.opportunity_id.project_manager_id.id if self.order_id.opportunity_id else False
        values['user_id'] = project_manager_id or False
        return values
    
    def _timesheet_create_project(self):
        project = super()._timesheet_create_project()
        project_uom = self.company_id.project_time_mode_id
        uom_unit = self.env.ref('uom.product_uom_unit')
        uom_hour = self.env.ref('uom.product_uom_hour')

        # dict of inverse factors for each relevant UoM found in SO
        factor_inv_per_id = {
            uom.id: uom.factor_inv
            for uom in self.order_id.order_line.product_uom
            if uom.category_id == project_uom.category_id
        }
        # if sold as units, assume hours for time allocation
        factor_inv_per_id[uom_unit.id] = uom_hour.factor_inv

        allocated_hours = 0.0
        # method only called once per project, so also allocate hours for
        # all lines in SO that will share the same project
        # for line in self.order_id.order_line:
        #     if line.is_service \
        #             and line.product_id.service_tracking in ['task_in_project', 'project_only'] \
        #             and line.product_id.project_template_id == self.product_id.project_template_id \
        #             and line.product_uom.id in factor_inv_per_id:
        #         uom_factor = project_uom.factor * factor_inv_per_id[line.product_uom.id]
        #         allocated_hours += line.product_uom_qty * uom_factor

        project.write({
            'allocated_hours': allocated_hours,
            'allow_timesheets': True,
        })
        return project
    
    def write(self, values):
        result = super().write(values)
        for line in self:
            if line.task_id and line.product_id.type == 'service':
                line.task_id.write({'allocated_hours': 0.0})
        return result