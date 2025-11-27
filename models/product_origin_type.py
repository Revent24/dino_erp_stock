# --- dino_erp_stock/models/product_origin_type.py ---
# МОДЕЛЬ ПРОИСХОЖДЕНИЕ ТОВАРА
# (используется как выпадающий список в Категории товара)
#
# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DinoOriginType(models.Model):
    _name = 'product.origin.type'
    _description = 'Тип Происхождения Товара'
    _order = 'name'

    # ПОЛЕ: Наименование типа происхождения
    name = fields.Char(
        string="Название типа",
        required=True, 
        translate=True,
    )
    
    # ПОЛЕ: Описание типа происхождения
    comment = fields.Text(
        string="Описание",
        translate=True, # Включает поддержку мультиязычности
        help="Полное описание Типа Происхождения Товара."
    )
    #ПОЛЕ: Технический код типа происходждения
    code = fields.Char(
        string="Технический код", 
        readonly=True, # Поле только для чтения, генерируется автоматически
        help="Уникальный код для использования в Python-логике (например, 'purchase', 'service').",
    )
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Технический код должен быть уникальным!'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        """ Переопределяем метод create для генерации кода на основе ID. """
        
        # 1. Вызываем стандартный метод create для создания записи(ей)
        # и получения доступа к их ID.
        records = super().create(vals_list)

        # 2. Генерируем код для каждой созданной записи
        for record in records:
            if not record.code:
                # Генерация кода: префикс 'OT_' + ID записи
                new_code = 'OT_%s' % record.id
                record.code = new_code
                
        return records