# --- МОДЕЛЬ: СТРОКИ СПЕЦИФИКАЦИИ (BOM Lines)
# --- ФАЙЛ: \dino24_addons\dino_erp_stock\models\product_component_bom.py
#

from odoo import fields, models, _, api

class DinoBomLine(models.Model):
    _name = 'dino.bom.line'
    _description = 'BOM Line'

    # Ссылка на РОДИТЕЛЬСКИЙ компонент (Владелец этой спецификации)
    parent_component_id = fields.Many2one('dino.product.component', string=_('Parent Component'), required=True, ondelete='cascade')
    
    # 1. Базовый компонент (Из чего состоит, компонент-потомок)
    component_id = fields.Many2one('dino.product.component', string=_('Component'), required=True)
    
    # 2. Модификации (Варианты атрибутов выбранного компонента-потомка)
    modification_ids = fields.Many2many(
        'dino.attribute.value', 
        string=_('Modifications'),
        domain="[('attribute_id', 'in', valid_attribute_ids)]"
    )
    
    # Техническое поле для фильтрации модификаций (показываем только атрибуты выбранного компонента)
    valid_attribute_ids = fields.Many2many('dino.attribute', compute='_compute_valid_attributes')

    qty = fields.Float(string=_('Quantity'), default=1.0, required=True)
    
    # Валюта (берем от родителя для правильного отображения денег)
    currency_id = fields.Many2one(related='parent_component_id.currency_id', readonly=True)
    
    # Цена (Пока берется базовая цена компонента)
    cost = fields.Monetary(string=_('Unit Cost'), compute='_compute_cost', currency_field='currency_id', store=True)
    
    # Сумма строки
    total_cost = fields.Monetary(string=_('Subtotal'), compute='_compute_total_cost', currency_field='currency_id', store=True)

    @api.depends('component_id')
    def _compute_valid_attributes(self):
        for line in self:
            if line.component_id:
                # Находим атрибуты, которые есть у вложенного компонента
                line.valid_attribute_ids = line.component_id.attribute_line_ids.mapped('attribute_id')
            else:
                line.valid_attribute_ids = False

    @api.depends('component_id.cost') 
    def _compute_cost(self):
        for line in self:
            # Логика: цена берется из карточки выбранного компонента
            line.cost = line.component_id.cost if line.component_id else 0.0

    @api.depends('qty', 'cost')
    def _compute_total_cost(self):
        for line in self:
            line.total_cost = line.qty * line.cost

# --- END ---