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

    # Добавляем поле заметок (Text для простого текста, translate=True для перевода самого текста заметки)
    description = fields.Html(string=_('Internal Notes'), translate=True)