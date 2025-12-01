from odoo import fields, models, _, api

class DinoBom(models.Model):
    # ... (Шапка BOM без изменений) ...
    _name = 'dino.bom'
    _description = 'Bill of Materials'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(default=True)
    name = fields.Char(string=_('Reference'), required=True, default='New', copy=False)
    version = fields.Char(string=_('Version'), default='1.0')
    
    component_id = fields.Many2one('dino.product.component', string=_('Component'), required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='component_id.currency_id', store=True, string=_('Currency'), readonly=True)
    
    attribute_value_ids = fields.Many2many(
        'dino.attribute.value', 
        string=_('Apply on Variants'),
        domain="[('attribute_id', 'in', available_attribute_ids)]"
    )
    available_attribute_ids = fields.Many2many('dino.attribute', compute='_compute_available_attributes')
    
    line_ids = fields.One2many('dino.bom.line', 'bom_id', string=_('Components'))
    total_cost = fields.Monetary(string=_('Total Cost'), compute='_compute_total_cost', currency_field='currency_id', store=True)

    @api.depends('component_id')
    def _compute_available_attributes(self):
        for bom in self:
            if bom.component_id:
                bom.available_attribute_ids = bom.component_id.attribute_line_ids.mapped('attribute_id')
            else:
                bom.available_attribute_ids = False

    @api.depends('line_ids.total_cost')
    def _compute_total_cost(self):
        for bom in self:
            bom.total_cost = sum(line.total_cost for line in bom.line_ids)


class DinoBomLine(models.Model):
    _name = 'dino.bom.line'
    _description = 'Bill of Materials Line'

    bom_id = fields.Many2one('dino.bom', string=_('BOM'), required=True, ondelete='cascade')
    component_id = fields.Many2one('dino.product.component', string=_('Component'), required=True)
    
    # === ИЗМЕНЕНИЕ ЗДЕСЬ ===
    # Теперь выбираем Значения Атрибутов (12 мм, 14 мм), а не Компоненты
    modification_ids = fields.Many2many(
        'dino.attribute.value', 
        string=_('Modifications'),
        domain="[('attribute_id', 'in', valid_attribute_ids)]" # Фильтр только по атрибутам этого компонента
    )
    
    # Техническое поле для фильтрации выпадающего списка модификаций
    valid_attribute_ids = fields.Many2many('dino.attribute', compute='_compute_valid_attributes')

    qty = fields.Float(string=_('Quantity'), default=1.0, required=True)
    currency_id = fields.Many2one(related='bom_id.currency_id', readonly=True)
    
    # Пока берем цену самого компонента. 
    # (Позже можно добавить наценку за атрибут в модель значений, если цена 12мм отличается от 14мм)
    cost = fields.Monetary(string=_('Unit Cost'), related='component_id.cost', currency_field='currency_id', readonly=True)
    total_cost = fields.Monetary(string=_('Subtotal'), compute='_compute_total_cost', currency_field='currency_id', store=True)

    @api.depends('component_id')
    def _compute_valid_attributes(self):
        for line in self:
            if line.component_id:
                # Находим, какие атрибуты есть у выбранного компонента (например, только "Длина")
                line.valid_attribute_ids = line.component_id.attribute_line_ids.mapped('attribute_id')
            else:
                line.valid_attribute_ids = False

    @api.depends('qty', 'cost')
    def _compute_total_cost(self):
        for line in self:
            # Сейчас цена едина для всех модификаций (берется из родителя)
            # Если нужно будет сделать разную цену для "12мм" и "14мм", 
            # нам придется добавить поле price_extra в модель dino.attribute.value
            line.total_cost = line.qty * line.cost