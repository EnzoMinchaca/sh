from odoo import models, fields, tools

class HrEmployeeSkillReport(models.BaseModel):
    _inherit = 'hr.employee.skill.report'

    fecha_inicio = fields.Date(string="Fecha de Inicio", store=True, readonly=False)
    fecha_fin = fields.Date(string="Fecha de Fin", store=True, readonly=False)
    puesto = fields.Many2one(
        'hr.job', 
        string="Puesto", 
        related='employee_id.job_id', 
        store=True, 
    )
    fecha_renovacion = fields.Date(string="Fecha de Renovación", store=True, readonly=False)
    archivo_nombre = fields.Char(string="Nombre del Archivo", store=True)
    
    custom_order = fields.Integer(string="Orden Personalizado", readonly=True)
    
    nombre_compania = fields.Char(string="Nombre de compañía", store=True, readonly=False)
    personalizado_texto = fields.Char(string="Genérico texto", store=True, readonly=False)
    personalizado_numerico = fields.Integer(string="Genérico numero", group_operator=False, store=True, readonly=False)
    
    #esto es para descargar el pdf que se adjunto para cada registro de hr.employe.skill
    def action_download_attachment(self):
        for record in self:
            attachment = self.env['ir.attachment'].search([
                ('id', '>', 0), #unicamente con esta condicion me dejaba traerme los registros, sin esto no me trae nada
                ('res_model', '=', 'hr.employee.skill'),
                ('res_id', '=', record.id),
            ], limit=1)
            
            if attachment:
                archivo_nombre = record.archivo_nombre or 'archivo'
                return {
                    'type': 'ir.actions.act_url',
                    'url': f'/web/content/{attachment.id}?download=true&filename={archivo_nombre}',
                    'target': 'self',
                }
            else:   #por si a uno no le cargaron un archivo, esto es para que no se rompa
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Error',
                        'message': 'No se ha encontrado un archivo adjunto para este registro.',
                        'type': 'danger',
                        'sticky': False,
                    },
                }
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute(f"""
        CREATE OR REPLACE VIEW {self._table} AS (
            SELECT
                s.id AS id,
                e.id AS employee_id,
                e.company_id AS company_id,
                e.department_id AS department_id,
                s.skill_id AS skill_id,
                s.skill_type_id AS skill_type_id,
                sl.level_progress / 100.0 AS level_progress,
                sl.name AS skill_level,
                s.puesto AS puesto,
                s.fecha_inicio AS fecha_inicio,
                s.fecha_fin AS fecha_fin,
                s.fecha_renovacion AS fecha_renovacion,
                s.archivo_nombre AS archivo_nombre,
                s.nombre_compania AS nombre_compania,
                s.personalizado_texto AS personalizado_texto,
                s.personalizado_numerico AS personalizado_numerico,
                CASE 
                    WHEN s.skill_type_id IN (
                        SELECT id FROM hr_skill_type WHERE name = 'Curriculum'
                    ) 
                    AND s.skill_id IN (
                        SELECT id FROM hr_skill WHERE name = 'Curriculum'
                    )
                    THEN 0 -- Prioridad más alta
                    ELSE 1 -- Otros registros
                END AS custom_order
            FROM hr_employee e
            LEFT OUTER JOIN hr_employee_skill s ON e.id = s.employee_id
            LEFT OUTER JOIN hr_skill_level sl ON sl.id = s.skill_level_id
            WHERE NOT (
                s.skill_type_id IN (
                    SELECT id FROM hr_skill_type WHERE name = 'Curriculum'
                )
                AND s.skill_id IN (
                    SELECT id FROM hr_skill WHERE name = 'Curriculum'
                )
                AND NOT EXISTS (
                    SELECT 1
                    FROM ir_attachment a
                    WHERE a.res_model = 'hr.employee.skill'
                    AND a.res_id = s.id
                    AND a.type = 'binary'
                )
            )
        )
        """)
        
        # trigger para actualizar las fechas
        self.env.cr.execute(f"""
        CREATE OR REPLACE FUNCTION {self._table}_update_trigger()
        RETURNS trigger AS $$
        BEGIN
            UPDATE hr_employee_skill
            SET fecha_inicio = NEW.fecha_inicio,
                fecha_fin = NEW.fecha_fin,
                fecha_renovacion = NEW.fecha_renovacion,
                nombre_compania = NEW.nombre_compania,
                personalizado_texto = NEW.personalizado_texto,
                personalizado_numerico = NEW.personalizado_numerico
            WHERE id = NEW.id;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER {self._table}_update
        INSTEAD OF UPDATE ON {self._table}
        FOR EACH ROW
        EXECUTE FUNCTION {self._table}_update_trigger();
        """)
