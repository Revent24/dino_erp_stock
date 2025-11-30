# --- МОДУЛЬ: КОМПОНЕНТЫ
# --- \dino24_addons\dino_erp_stock\models\product_component.py 
#
from odoo import fields, models, _, api

class DinoProductComponent(models.Model):
    _name = 'dino.product.component'
    _description = 'Dino Product Component'
    _inherit = ['image.mixin', 'mail.thread', 'mail.activity.mixin'] 

    active = fields.Boolean('Active', default=True)
    
    # Используем _() чтобы Odoo точно знал, что это метка для перевода
    name = fields.Char(string=_('Component Name'), required=True, tracking=True, translate=True)
    code = fields.Char(string=_('Internal Reference'), copy=False, tracking=True)

    qty_available = fields.Float(string=_('On Hand'), default=0.0) 
    
    currency_id = fields.Many2one('res.currency', string=_('Currency'), 
                                  default=lambda self: self.env.company.currency_id)
    
    cost = fields.Monetary(string=_('Cost'), currency_field='currency_id', default=0.0)
    is_favorite = fields.Boolean(string=_('Favorite'))

    _sql_constraints = [
        ('code_unique', 'unique (code)', 'The internal reference must be unique.'),
    ]
    
    def toggle_is_favorite(self):
        for rec in self:
            rec.is_favorite = not rec.is_favorite
    
    # Вложенная таблица Атрибуты
    attribute_line_ids = fields.One2many('dino.component.attribute.line', 'component_id', string=_('Attributes'))

    # Связь с BOM
    bom_ids = fields.One2many('dino.bom', 'component_id', string=_('BOMs'))
    bom_count = fields.Integer(string=_('BOM Count'), compute='_compute_bom_count')

    @api.depends('bom_ids')
    def _compute_bom_count(self):
        for rec in self:
            rec.bom_count = len(rec.bom_ids)

    def action_view_boms(self):
        self.ensure_one()
        return {
            'name': _('Specifications'),
            'type': 'ir.actions.act_window',
            'res_model': 'dino.bom',
            'view_mode': 'list,form',
            'domain': [('component_id', '=', self.id)],
            'context': {'default_component_id': self.id},
        }

    # Поле заметок (Htm для форматируемого текста, translate=True для перевода самого текста заметки)
    description = fields.Html(string=_('Internal Notes'), translate=True)