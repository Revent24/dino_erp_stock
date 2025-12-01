# --- МОДЕЛЬ: АТРИБУТЫ КОМПОНЕНТА
# --- \dino24_addons\dino_erp_stock\models\product_component_attribute.py 
#

from odoo import fields, models, _, api

class DinoAttribute(models.Model):
    _name = 'dino.attribute'
    _description = 'Component Attribute'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string=_('Attribute Name'), required=True, translate=True)
    
    # Код: Только для чтения, по умолчанию 'New', автозаполняется
    code = fields.Char(string=_('Code'), required=True, default='New', readonly=True, copy=False)
    
    value_ids = fields.One2many('dino.attribute.value', 'attribute_id', string=_('Values'))

    # 1. Проверка на уникальность
    _sql_constraints = [
        ('code_unique', 'unique (code)', 'Attribute Code must be unique!'),
        ('name_uniq', 'unique (name)', 'Attribute Name must be unique!'),
    ]

    # 2. Логика автогенерации кода (A001, A002...)
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', 'New') == 'New':
                # Берем следующий номер из последовательности
                vals['code'] = self.env['ir.sequence'].next_by_code('dino.attribute') or 'New'
        return super().create(vals_list)


class DinoAttributeValue(models.Model):
    _name = 'dino.attribute.value'
    _description = 'Attribute Value'
    _order = 'sequence, id'

    name = fields.Char(string=_('Value Name'), required=True, translate=True)
    
    # Новые поля для цифр и единиц измерения
    numeric_value = fields.Float(string=_('Numeric Value'), default=0.0)
    uom_id = fields.Many2one('uom.uom', string=_('Units')) # Ссылка на стандартные единицы Odoo
    
    sequence = fields.Integer(string=_('Sequence'), default=10)
    attribute_id = fields.Many2one('dino.attribute', string=_('Attribute'), required=True, ondelete='cascade')
    
    def name_get(self):
        # Формируем красивое имя для отображения в тегах: "Длинный (155 mm)"
        result = []
        for record in self:
            name = record.name
            if record.numeric_value:
                if record.uom_id:
                    name = f"{name} ({record.numeric_value} {record.uom_id.name})"
                else:
                    name = f"{name} ({record.numeric_value})"
            result.append((record.id, name))
        return result


class DinoComponentAttributeLine(models.Model):
    _name = 'dino.component.attribute.line'
    _description = 'Component Attribute Line'
    _order = 'attribute_id, id'

    # Исправление хлебных крошек: теперь заголовок будет именем атрибута
    display_name = fields.Char(related='attribute_id.name', string="Attribute Name", store=True)

    component_id = fields.Many2one('dino.product.component', string=_('Component'), required=True, ondelete='cascade')
    attribute_id = fields.Many2one('dino.attribute', string=_('Attribute'), required=True)
    value_ids = fields.Many2many('dino.attribute.value', string=_('Values'))