# --- МОДЕЛЬ: НОМЕНКЛАТУРА (ИСПОЛНЕНИЕ / КОНКРЕТНЫЙ ТОВАР)
# --- ФАЙЛ: models/dino_nomenclature.py
#

from odoo import fields, models, _, api

class DinoNomenclature(models.Model):
    _name = 'dino.nomenclature'
    _description = 'Nomenclature (Variant/Execution)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'fullname' # Чтобы в ссылках отображалось полное имя
    _order = 'fullname'

    # === СВЯЗИ ===
    # Дата создания (обязательное поле, можно редактировать, без времени)
    create_date = fields.Date(string=_('Created on'), required=True, default=fields.Date.context_today)
    
    # Родитель (Семейство)
    component_id = fields.Many2one('dino.component', string=_('Component Family'), required=True, ondelete='cascade', tracking=True)
    
    # Категория родителя
    category_id = fields.Many2one(related='component_id.category_id', string=_('Category'), readonly=True, store=True)

    # Единица измерения (берется от родителя, только чтение)
    uom_id = fields.Many2one(related='component_id.uom_id', string=_('Unit of Measure'), readonly=True)

    # Скрыть спецификацию (Берем значение из настройки категории)
    hide_specification = fields.Boolean(related='category_id.hide_specification', readonly=True)

    # Тип происхождения (Берем значение из настройки категории)
    origin_type = fields.Selection(related='category_id.origin_type', string=_('Origin Type'), readonly=True, store=True)

    # === НАИМЕНОВАНИЕ ===
    # Суффикс - уникальная характеристика этого исполнения (напр. "810 мм" или "Оцинкованный")
    # Необязательно для уникальных деталей без вариантов
    name = fields.Char(string=_('Execution Name'), required=False, tracking=True, translate=True)
    
    # Полное имя = Родитель + Суффикс (напр. "Комплект ручек 810 мм")
    fullname = fields.Char(string=_('Full Name'), compute='_compute_fullname', store=True, index=True)

    # Артикул (Уникальный код детали)
    code = fields.Char(string=_('Reference'), copy=False, tracking=True)

    # === ЭКОНОМИКА ===
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    cost = fields.Monetary(string=_('Purchase Price'), currency_field='currency_id', default=0.0, tracking=True, readonly=True, help="Price from latest purchase document")
    qty_available = fields.Float(string=_('On Hand'), default=0.0, tracking=True)

    # === ВЛОЖЕННЫЕ ТАБЛИЦЫ (Создадим модели для них на следующих шагах) ===
    # Параметры (Длина=810, Вес=0.5)
    parameter_ids = fields.One2many('dino.parameter', 'nomenclature_id', string=_('Parameters'))
    
    # Спецификация (Состав)
    bom_line_ids = fields.One2many('dino.bom.line', 'parent_nomenclature_id', string=_('Bill of Materials'))

    # Полная стоимость = Цена закупки + Сумма материалов по BOM
    total_cost = fields.Monetary(string=_('Total Cost'), compute='_compute_total_cost', currency_field='currency_id', store=True)

    # Назначение исполнения (краткая заметка к названию)
    purpose = fields.Char(string=_('Purpose'), translate=True, help="Short description of the execution")

    # Внутренние заметки
    description = fields.Html(string=_('Internal Notes'), translate=True)
    
    # === СВЯЗИ С ДОКУМЕНТАМИ ПОСТАВЩИКОВ ===
    # Количество связанных позиций в документах поставщиков (для смарт-кнопки)
    supplier_line_count = fields.Integer(compute='_compute_supplier_line_count')
    
    # === ЛОГИКА ===
    
    def _compute_supplier_line_count(self):
        """Подсчитывает количество связанных позиций в документах поставщиков"""
        for rec in self:
            # Ищем в модуле operations, если он установлен
            if 'dino.operation.document.specification' in self.env:
                rec.supplier_line_count = self.env['dino.operation.document.specification'].search_count([
                    ('nomenclature_id', '=', rec.id)
                ])
            else:
                rec.supplier_line_count = 0
    
    def action_view_supplier_prices(self):
        """Открывает список цен из документов поставщиков"""
        self.ensure_one()
        
        return {
            'name': _('Price History'),
            'type': 'ir.actions.act_window',
            'res_model': 'dino.operation.document.specification',
            'view_mode': 'list',
            'view_id': self.env.ref('dino_erp_operations.view_specification_price_history_tree').id,
            'domain': [('nomenclature_id', '=', self.id)],
            'context': {'create': False, 'edit': False},
        }
    
    # Автоматическая склейка имени
    @api.depends('component_id.name', 'name')
    def _compute_fullname(self):
        for rec in self:
            if rec.component_id and rec.name:
                rec.fullname = f"{rec.component_id.name} {rec.name}"
            else:
                rec.fullname = rec.name or rec.component_id.name

    # Расчет полной стоимости: цена закупки + материалы
    @api.depends('cost', 'bom_line_ids.total_cost')
    def _compute_total_cost(self):
        for rec in self:
            materials_sum = sum(line.total_cost for line in rec.bom_line_ids)
            rec.total_cost = rec.cost + materials_sum
    
    def _recompute_parent_assemblies(self):
        """
        Итеративный метод пересчета стоимости (снизу-вверх).
        Вместо рекурсии используется цикл while, который поднимается по уровням вложенности.
        На каждом уровне происходит жесткая фиксация цен в БД через SQL.
        """
        if not self:
            return

        # Начинаем с текущих номенклатур (у которых изменилась цена или структура)
        current_level_nomenclatures = self
        
        # Защита от бесконечных циклов (если есть циклические зависимости в BOM)
        max_iterations = 100
        iteration = 0
        
        # Технические поля для SQL запросов
        bom_line_model = self.env['dino.bom.line']
        m2m_table = bom_line_model._fields['nomenclature_ids'].relation
        m2m_col1 = bom_line_model._fields['nomenclature_ids'].column1 # bom_line_id
        m2m_col2 = bom_line_model._fields['nomenclature_ids'].column2 # nomenclature_id

        while current_level_nomenclatures and iteration < max_iterations:
            iteration += 1
            
            # 1. ОБНОВЛЕНИЕ НОМЕНКЛАТУР ТЕКУЩЕГО УРОВНЯ
            # Пересчитываем total_cost = cost + sum(bom_lines)
            # Делаем это SQL-запросом, чтобы гарантировать, что в БД лежат актуальные цифры.
            # Для самого первого уровня (компонентов) это обновит total_cost на основе их новой cost.
            # Для следующих уровней (сборок) это обновит total_cost на основе обновленных BOM-линий.
            
            ids_tuple = tuple(current_level_nomenclatures.ids)
            self.env.cr.execute("""
                UPDATE dino_nomenclature n
                SET total_cost = n.cost + COALESCE((
                    SELECT SUM(bl.total_cost)
                    FROM dino_bom_line bl
                    WHERE bl.parent_nomenclature_id = n.id
                ), 0)
                WHERE n.id IN %s
            """, (ids_tuple,))
            
            # Сбрасываем кэш, чтобы UI увидел изменения
            current_level_nomenclatures.invalidate_recordset(['total_cost'])
            
            # 2. ПОИСК ЗАВИСИМОСТЕЙ (Где используются эти номенклатуры?)
            # Ищем строки BOM, в которых участвуют текущие номенклатуры как компоненты/аналоги
            bom_lines = bom_line_model.sudo().search([
                ('nomenclature_ids', 'in', current_level_nomenclatures.ids)
            ])
            
            if not bom_lines:
                # Если эти номенклатуры нигде не используются, цепочка завершена
                break
                
            # 3. ОБНОВЛЕНИЕ СТРОК BOM
            # Пересчитываем стоимость строк BOM, ссылающихся на текущий уровень.
            # cost = Среднее(total_cost аналогов)
            # total_cost = qty * cost
            
            bom_line_ids = tuple(bom_lines.ids)
            
            self.env.cr.execute(f"""
                WITH avg_costs AS (
                    SELECT rel.{m2m_col1} as bom_line_id, COALESCE(AVG(n.total_cost), 0) as avg_cost
                    FROM {m2m_table} rel
                    JOIN dino_nomenclature n ON rel.{m2m_col2} = n.id
                    WHERE rel.{m2m_col1} IN %s
                    GROUP BY rel.{m2m_col1}
                )
                UPDATE dino_bom_line bl
                SET 
                    cost = ac.avg_cost,
                    total_cost = bl.qty * ac.avg_cost
                FROM avg_costs ac
                WHERE bl.id = ac.bom_line_id
            """, (bom_line_ids,))
            
            # Сбрасываем кэш строк BOM
            bom_lines.invalidate_recordset(['cost', 'total_cost'])
            
            # 4. ПЕРЕХОД НА СЛЕДУЮЩИЙ УРОВЕНЬ
            # Родители этих строк BOM становятся "текущим уровнем" для следующей итерации
            next_level_parents = bom_lines.mapped('parent_nomenclature_id')
            current_level_nomenclatures = next_level_parents
    
    def write(self, vals):
        """При изменении cost или total_cost - пересчитываем всех родителей"""
        result = super().write(vals)
        
        # Если изменились cost или total_cost - запускаем пересчет вверх
        if 'cost' in vals or 'total_cost' in vals:
            self._recompute_parent_assemblies()
        
        return result

    # Метод для кнопки "Стрелочка"
    def action_open_form(self):
        self.ensure_one()
        return {
            'name': self.fullname,
            'type': 'ir.actions.act_window',
            'res_model': 'dino.nomenclature',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current', # Открыть в текущем окне 'current' (или 'new' для модального)
        }

    # === ЛОГИКА ОТОБРАЖЕНИЯ ИМЕНИ ===
    @api.depends('name', 'fullname')
    @api.depends_context('show_short_name') # Слушаем контекст из XML
    def _compute_display_name(self):
        for rec in self:
            # Если в контексте пришел флаг - показываем только суффикс (810 мм)
            if self.env.context.get('show_short_name'):
                rec.display_name = rec.name
            else:
                # Иначе показываем полное имя (Ручка внешняя 810 мм)
                rec.display_name = rec.fullname

    _sql_constraints = [
        # Нельзя создать два одинаковых суффикса внутри одного семейства
        ('name_uniq_per_component', 'unique (component_id, name)', 'The execution name must be unique within the component family!'),
        # Артикул должен быть уникальным во всей системе
        ('code_unique', 'unique (code)', 'The Reference must be unique!'),
    ]



    # === SMART BUTTONS LOGIC ===
    
    # 1. Счетчик строк спецификации
    bom_count = fields.Integer(compute='_compute_bom_count')

    @api.depends('bom_line_ids')
    def _compute_bom_count(self):
        for rec in self:
            rec.bom_count = len(rec.bom_line_ids)

    # Действие: Открыть BOM на весь экран
    def action_view_bom(self):
        self.ensure_one()
        return {
            'name': _('Bill of Materials'),
            'type': 'ir.actions.act_window',
            'res_model': 'dino.bom.line',
            'view_mode': 'list,form',
            'domain': [('parent_nomenclature_id', '=', self.id)], # Показываем строки ЭТОЙ номенклатуры
            'context': {'default_parent_nomenclature_id': self.id}, # При создании новой строки подставляем родителя
        }

    # 1. Счетчик "Где используется"
    used_in_count = fields.Integer(string="Used In Count", compute='_compute_used_in_count')

    def _compute_used_in_count(self):
        for rec in self:
            # Ищем строки BOM, где в списке аналогов (nomenclature_ids) есть наш ID
            lines = self.env['dino.bom.line'].search([('nomenclature_ids', 'in', rec.id)])
            # Берем уникальных владельцев этих строк
            parents = lines.mapped('parent_nomenclature_id')
            rec.used_in_count = len(parents)

    # Действие для кнопки "Где используется"
    def action_view_used_in(self):
        self.ensure_one()
        # Находим те же записи
        lines = self.env['dino.bom.line'].search([('nomenclature_ids', 'in', self.id)])
        parent_ids = lines.mapped('parent_nomenclature_id').ids
        
        return {
            'name': _('Used In'),
            'type': 'ir.actions.act_window',
            'res_model': 'dino.nomenclature',
            'view_mode': 'list,form',
            'domain': [('id', 'in', parent_ids)], # Фильтр: показать только родителей
            'context': {'create': False},          # Запрещаем создавать там лишнее
        }

    # 2. Действие для кнопки "Родитель (Семейство)"
    def action_view_parent(self):
        self.ensure_one()
        return {
            'name': _('Component Family'),
            'type': 'ir.actions.act_window',
            'res_model': 'dino.component',
            'res_id': self.component_id.id, # ID нашего родителя
            'view_mode': 'form',
            'target': 'current',
        }

# --- END ---