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

    active = fields.Boolean(default=True)

    # === СВЯЗИ ===
    # Родитель (Семейство)
    component_id = fields.Many2one('dino.component', string=_('Component Family'), required=True, ondelete='cascade', tracking=True)
    
    # Единица измерения (берется от родителя, только чтение)
    uom_id = fields.Many2one(related='component_id.uom_id', string=_('Unit of Measure'), readonly=True)

    # === НАИМЕНОВАНИЕ ===
    # Суффикс - уникальная характеристика этого исполнения (напр. "810 мм" или "Оцинкованный")
    name = fields.Char(string=_('Execution Name'), required=True, tracking=True, translate=True)
    
    # Полное имя = Родитель + Суффикс (напр. "Комплект ручек 810 мм")
    fullname = fields.Char(string=_('Full Name'), compute='_compute_fullname', store=True, index=True)

    # Артикул (Уникальный код детали)
    code = fields.Char(string=_('Reference'), copy=False, tracking=True)

    # === ЭКОНОМИКА ===
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    cost = fields.Monetary(string=_('Cost'), currency_field='currency_id', default=0.0, tracking=True)
    qty_available = fields.Float(string=_('On Hand'), default=0.0, tracking=True)

    # === ВЛОЖЕННЫЕ ТАБЛИЦЫ (Создадим модели для них на следующих шагах) ===
    # Параметры (Длина=810, Вес=0.5)
    parameter_ids = fields.One2many('dino.parameter', 'nomenclature_id', string=_('Parameters'))
    
    # Спецификация (Состав)
    bom_line_ids = fields.One2many('dino.bom.line', 'parent_nomenclature_id', string=_('Bill of Materials'))

    # Стоимость материалов (Сумма BOM)
    material_cost = fields.Monetary(string=_('Material Cost'), compute='_compute_material_cost', currency_field='currency_id', store=True)

    # Назначение исполнения (краткая заметка к названию)
    purpose = fields.Char(string=_('Purpose'), translate=True, help="Short description of the execution")

    # Внутренние заметки
    description = fields.Html(string=_('Internal Notes'), translate=True)
    
    
    # === ЛОГИКА ===
    
    # Автоматическая склейка имени
    @api.depends('component_id.name', 'name')
    def _compute_fullname(self):
        for rec in self:
            if rec.component_id and rec.name:
                rec.fullname = f"{rec.component_id.name} {rec.name}"
            else:
                rec.fullname = rec.name or rec.component_id.name

    # Расчет стоимости по BOM
    @api.depends('bom_line_ids.total_cost')
    def _compute_material_cost(self):
        for rec in self:
            rec.material_cost = sum(line.total_cost for line in rec.bom_line_ids)

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

# --- END ---