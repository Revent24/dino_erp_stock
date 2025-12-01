# --- МОДЕЛЬ: КОМПОНЕНТ (СЕМЕЙСТВО / РОДИТЕЛЬ)
# --- ФАЙЛ: models/dino_component.py
#

from odoo import fields, models, _, api

class DinoComponent(models.Model):
    _name = 'dino.component'
    _description = 'Component Family'
    _inherit = ['image.mixin', 'mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(default=True)
    
    # Название семейства (напр. "Комплект ручек", "Винт М4")
    name = fields.Char(string=_('Family Name'), required=True, translate=True, tracking=True)
    
    # Категория (ссылка на стандартные категории Odoo)
    category_id = fields.Many2one('product.category', string=_('Category'), tracking=True)
    
    # Единица измерения (Общая для всех исполнений этого семейства)
    uom_id = fields.Many2one(
        'uom.uom', 
        string=_('Unit of Measure'), 
        required=True,
        default=lambda self: self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
    )

    # Связь с Исполнениями (детьми)
    nomenclature_ids = fields.One2many('dino.nomenclature', 'component_id', string=_('Nomenclatures'))

    is_favorite = fields.Boolean(string=_('Favorite'))

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Component Family name must be unique!'),
    ]

    def toggle_is_favorite(self):
        for rec in self:
            rec.is_favorite = not rec.is_favorite

# --- END ---