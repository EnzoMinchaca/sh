from odoo import tools

def restore_original_view(env):
    cr = env.cr  # Obtén el cursor desde el entorno
    tools.drop_view_if_exists(cr, 'hr_employee_skill_report')
    cr.execute("""
        CREATE OR REPLACE VIEW hr_employee_skill_report AS (
            SELECT
                row_number() OVER () AS id,
                e.id AS employee_id,
                e.company_id AS company_id,
                e.department_id AS department_id,
                s.skill_id AS skill_id,
                s.skill_type_id AS skill_type_id,
                sl.level_progress / 100.0 AS level_progress,
                sl.name AS skill_level
            FROM hr_employee e
            LEFT OUTER JOIN hr_employee_skill s ON e.id = s.employee_id
            LEFT OUTER JOIN hr_skill_level sl ON sl.id = s.skill_level_id
        )
    """)
