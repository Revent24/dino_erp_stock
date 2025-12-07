# --- МОДЕЛЬ: СТРОКИ СПЕЦИФИКАЦИИ (BOM)
# --- ФАЙЛ: models/dino_bom.py
#

from odoo import fields, models, _, api

class DinoBomLine(models.Model):
    _name = 'dino.bom.line'
    _description = 'BOM Line'
    _order = 'sequence, id'  # <-- Сначала ручная сортировка, потом по ВID

    # Поле для сортировки
    sequence = fields.Integer(string=_('Sequence'), default=10)

    # 1. К кому относится эта строка (Владелец спецификации)
    parent_nomenclature_id = fields.Many2one('dino.nomenclature', string=_('Parent Nomenclature'), required=True, ondelete='cascade')
    
    # 2. Фильтр: Выбор Семейства (Напр. "Винт М4")
    component_id = fields.Many2one('dino.component', string=_('Component Family'), required=True)
    
    # 3. Выбор: Конкретные Исполнения (Напр. "12 мм", "14 мм")
    # Фильтруем их: показываем только детей выбранного component_id
    nomenclature_ids = fields.Many2many(
        'dino.nomenclature', 
        string=_('Executions / Analogs'),
        domain="[('component_id', '=', component_id)]"
    )
    
    qty = fields.Float(string=_('Quantity'), default=1.0, required=True)
    
    # Валюта (берем от родителя)
    currency_id = fields.Many2one(related='parent_nomenclature_id.currency_id', readonly=True)
    
    # Цена (Средняя по выбранным исполнениям)
    cost = fields.Monetary(string=_('Unit Cost'), compute='_compute_cost', currency_field='currency_id', store=True)
    
    # Сумма
    total_cost = fields.Monetary(string=_('Subtotal'), compute='_compute_total_cost', currency_field='currency_id', store=True)

    # === МЕТОД ДЛЯ КНОПКИ (ОТКРЫТИЕ АНАЛОГОВ) ===
    def action_open_analogs(self):
        self.ensure_one()
        if not self.nomenclature_ids:
            return # Если ничего не выбрано - ничего не делаем

        # Получаем ID выбранных аналогов
        analog_ids = self.nomenclature_ids.ids

        # Сценарий 1: Выбран только один - открываем его Форму
        if len(analog_ids) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'dino.nomenclature',
                'res_id': analog_ids[0],
                'view_mode': 'form',
                'target': 'current',
            }
        
        # Сценарий 2: Выбрано несколько - открываем их Список
        else:
            return {
                'name': _('Selected Analogs'),
                'type': 'ir.actions.act_window',
                'res_model': 'dino.nomenclature',
                'domain': [('id', 'in', analog_ids)],
                'view_mode': 'list,form',
                'target': 'current',
            }
    # ============================================

    @api.depends('nomenclature_ids.total_cost')
    def _compute_cost(self):
        """Рекурсивный расчет: цена = средняя полная стоимость аналогов"""
        for line in self:
            total_price = 0.0
            count = 0
            
            # Складываем полную стоимость всех выбранных исполнений
            for nom in line.nomenclature_ids:
                # total_cost уже включает цену закупки + материалы (рекурсивно)
                total_price += nom.total_cost
                count += 1
            
            # Считаем среднее
            line.cost = total_price / count if count > 0 else 0.0

    @api.depends('qty', 'cost')
    def _compute_total_cost(self):
        for line in self:
            line.total_cost = line.qty * line.cost

# --- END ---