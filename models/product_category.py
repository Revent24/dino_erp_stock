# 
#     МОДЕЛЬ КАТЕГОРИЯ ТОВАРА
# --- dino_erp_stock/models/product_category.py ---


from odoo import models, fields


class ProductCategory(models.Model):
    _inherit = 'product.category'

    name = fields.Char(translate=True)

    dino_origin_type_id = fields.Many2one( 
        'product.origin.type', 
        string="Тип происхождения",
        required=True,
        ondelete='restrict', 
    )
    
    dino_origin_type_code = fields.Char(
        related='dino_origin_type_id.code',
        string="Технический код происхождения",
        readonly=True,
        store=True,
    )