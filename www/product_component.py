# --- МОДЕЛЬ: КОМПОНЕНТЫ (ОСНОВНАЯ СУЩНОСТЬ)
# --- ФАЙЛ: \dino24_addons\dino_erp_stock\models\product_component.py
#

from odoo import fields, models, _, api

class DinoProductComponent(models.Model):
    _name = 'dino.product.component'
    _description = 'Dino Product Component'
    _inherit = ['image.mixin', 'mail.thread', 'mail.activity.mixin'] 

    active = fields.Boolean('Active', default=True)
    
    name = fields.Char(string=_('Component Name'), required=True, tracking=True, translate=True)
    code = fields.Char(string=_('Internal Reference'), copy=False, tracking=True)

    qty_available = fields.Float(string=_('On Hand'), default=0.0) 
    
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                  default=lambda self: self.env.company.currency_id)
    
    # Собственная цена компонента (например, цена закупки или производства)
    cost = fields.Monetary(string=_('Cost'), currency_field='currency_id', default=0.0)
    
    is_favorite = fields.Boolean(string=_('Favorite'))

    # === АТРИБУТЫ (Связь с моделью строк атрибутов) ===
    attribute_line_ids = fields.One2many('dino.component.attribute.line', 'component_id', string=_('Attributes'))

    # === СПЕЦИФИКАЦИЯ (Встроенная) ===
    # Ссылка на строки BOM, где этот компонент является Родителем
    bom_line_ids = fields.One2many('dino.bom.line', 'parent_component_id', string=_('Bill of Materials'))
    
    # Стоимость материалов (Сумма всех строк спецификации)
    # Это поле показывает, сколько стоит собрать этот компонент из других
    material_cost = fields.Monetary(string=_('Material Cost'), compute='_compute_material_cost', currency_field='currency_id', store=True)

    # Поле для заметок (HTML редактор)
    description = fields.Html(string=_('Internal Notes'), translate=True)

    _sql_constraints = [
        ('code_unique', 'unique (code)', 'The internal reference must be unique.'),
    ]
    
    @api.depends('bom_line_ids.total_cost')
    def _compute_material_cost(self):
        for rec in self:
            rec.material_cost = sum(line.total_cost for line in rec.bom_line_ids)
            
    def toggle_is_favorite(self):
        for rec in self:
            rec.is_favorite = not rec.is_favorite

# --- END ---