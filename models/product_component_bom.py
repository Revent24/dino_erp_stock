#
# --- МОДУЛЬ: СПЕЦИФИКАЦИИ
# --- \dino24_addons\dino_erp_stock\models\product_component_bom.py
#


from odoo import fields, models, _, api

class DinoBom(models.Model):
    _name = 'dino.bom'
    _description = 'Bill of Materials'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(default=True)
    name = fields.Char(string=_('Reference'), required=True, default='New', copy=False)
    version = fields.Char(string=_('Version'), default='1.0')
    
    # Родительский компонент (Что производим)
    component_id = fields.Many2one('dino.product.component', string=_('Component'), required=True, ondelete='cascade')
    
    # Валюта (берется от компонента для правильного отображения денег)
    currency_id = fields.Many2one(related='component_id.currency_id', store=True, string=_('Currency'), readonly=True)
    
    # === ВАРИАНТЫ ===
    # Если спецификация только для конкретной Длины/Цвета
    attribute_value_ids = fields.Many2many(
        'dino.attribute.value', 
        string=_('Apply on Variants'),
        domain="[('attribute_id', 'in', available_attribute_ids)]"
    )
    # Техническое поле для фильтрации атрибутов в форме
    available_attribute_ids = fields.Many2many('dino.attribute', compute='_compute_available_attributes')

    # === СОСТАВ ===
    line_ids = fields.One2many('dino.bom.line', 'bom_id', string=_('Components'))

    # Итоговая стоимость
    total_cost = fields.Monetary(string=_('Total Cost'), compute='_compute_total_cost', currency_field='currency_id', store=True)

    @api.depends('component_id')
    def _compute_available_attributes(self):
        for bom in self:
            if bom.component_id:
                # Показываем только те атрибуты, которые есть у этого компонента
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
    
    # Компонент в составе
    component_id = fields.Many2one('dino.product.component', string=_('Component'), required=True)
    
    # === АНАЛОГИ ===
    # Выбор нескольких альтернатив. 
    alternative_component_ids = fields.Many2many(
        'dino.product.component', 
        'dino_bom_line_alternatives_rel', 
        'line_id', 'component_id',
        string=_('Alternatives')
    )
    
    qty = fields.Float(string=_('Quantity'), default=1.0, required=True)
    
    # Валюта и цена
    currency_id = fields.Many2one(related='bom_id.currency_id', readonly=True)
    cost = fields.Monetary(string=_('Unit Cost'), related='component_id.cost', currency_field='currency_id', readonly=True)
    
    total_cost = fields.Monetary(string=_('Subtotal'), compute='_compute_total_cost', currency_field='currency_id', store=True)

    @api.depends('qty', 'cost', 'alternative_component_ids')
    def _compute_total_cost(self):
        for line in self:
            # БАЗОВАЯ ЛОГИКА: Цена основного компонента * кол-во
            # СЮДА позже допишем логику среднего арифметического, если выбраны аналоги
            line.total_cost = line.qty * line.cost