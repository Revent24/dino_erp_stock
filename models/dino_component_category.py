# --- МОДЕЛЬ: РАСШИРЕНИЕ КАТЕГОРИЙ (Настройка видимости BOM)
# --- ФАЙЛ: models/dino_component_category.py

from odoo import fields, models, _

class ProductCategory(models.Model):
    _inherit = 'product.category'

    # Галочка, которая будет управлять видимостью вкладки BOM
    hide_specification = fields.Boolean(string=_('Hide Specification'), default=False)

    # Тип происхождения
    origin_type = fields.Selection([
        ('purchase', 'Purchase'),          # Закупка
        ('subcontract', 'Subcontracting'), # Субподряд
        ('service', 'Service'),            # Услуга
        ('production', 'Manufacturing')    # Производство
    ], string=_('Origin Type'), default='purchase', help="Defines the origin of the component family.")

    # === НОВЫЕ СЧЕТЧИКИ ===
    dino_component_count = fields.Integer(compute='_compute_dino_counts')
    dino_nomenclature_count = fields.Integer(compute='_compute_dino_counts')

    def _compute_dino_counts(self):
        for rec in self:
            # Считаем Семейства (прямая связь category_id)
            rec.dino_component_count = self.env['dino.component'].search_count([('category_id', 'child_of', rec.id)])
            
            # Считаем Номенклатуру (связь через component_id.category_id)
            # Используем child_of, чтобы захватить подкатегории
            rec.dino_nomenclature_count = self.env['dino.nomenclature'].search_count([('component_id.category_id', 'child_of', rec.id)])

    # === КНОПКИ ===
    def action_view_dino_components(self):
        self.ensure_one()
        return {
            'name': _('Families'),
            'type': 'ir.actions.act_window',
            'res_model': 'dino.component',
            'view_mode': 'list,form',
            'domain': [('category_id', 'child_of', self.id)],
            'context': {'default_category_id': self.id},
        }

    def action_view_dino_nomenclatures(self):
        self.ensure_one()
        return {
            'name': _('Nomenclatures'),
            'type': 'ir.actions.act_window',
            'res_model': 'dino.nomenclature',
            'view_mode': 'list,form',
            'domain': [('component_id.category_id', 'child_of', self.id)],
            # context тут сложнее, так как связь через родителя, оставим пустым
        }