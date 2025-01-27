from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class ProjectCategory(models.Model):
    _name = 'project.category'
    _description = 'Categorías de proyectos'
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char(string='Nombre', required=True)
    complete_name = fields.Char(string='Nombre completo', compute='_compute_complete_name', store=True, recursive=True)
    parent_id = fields.Many2one('project.category', string='Categoría principal', index=True)
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('project.category', 'parent_id', string='Categorías secundarias')
    project_count = fields.Integer(string='# Proyectos', compute='_compute_project_count', help='El número de proyectos bajo esta categoría (No considera las categorías secundarias)')

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = '%s / %s' % (category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name
    
    def _compute_project_count(self):
        read_group_res = self.env['project.project']._read_group([('categ_id', 'child_of', self.ids)], ['categ_id'], ['__count'])
        group_data = {categ.id: count for categ, count in read_group_res}
        for categ in self:
            project_count = 0
            for sub_categ_id in categ.search([('id', 'child_of', categ.ids)]).ids:
                project_count += group_data.get(sub_categ_id, 0)
            categ.project_count = project_count
    
    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError('No puedes crear categorías recursivas.')

    @api.model
    def name_create(self, name):
        category = self.create({'name': name})
        return category.id, category.display_name

    @api.depends_context('hierarchical_naming')
    def _compute_display_name(self):
        if self.env.context.get('hierarchical_naming', True):
            return super()._compute_display_name()
        for record in self:
            record.display_name = record.name
