# 
# --- МОДУЛЬ: КОМПОНЕНТЫ
# --- \dino24_addons\dino_erp_stock\models\product_component.py 
#
from odoo import fields, models

class DinoProductComponent(models.Model):
    _name = 'dino.product.component'
    _description = 'Dino Product Component'
    # Наследуем миксины для фото, чаттера и избранного
    _inherit = ['image.mixin', 'mail.thread'] 
    
    active = fields.Boolean('Active', default=True)
    name = fields.Char(string='Component Name', required=True, tracking=True)
    code = fields.Char(string='Internal Reference', copy=False, default='New', tracking=True)

    # Поля, добавленные по запросу:
    qty_available = fields.Float(string='On Hand', default=0.0) # В наличии
    
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                  default=lambda self: self.env.company.currency_id)
    cost = fields.Monetary(string='Cost', currency_field='currency_id', default=0.0) # Стоимость
    
    # Функциональность избранного
    is_favorite = fields.Boolean(string='Favorite')

    _sql_constraints = [
        ('code_unique', 'unique (code)', 'The internal reference must be unique.'),
    ]
    
    # Метод для переключения избранного (используется кнопкой в форме)
    def toggle_is_favorite(self):
        for rec in self:
            rec.is_favorite = not rec.is_favorite