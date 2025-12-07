# --- МАНИФЕСТ МОДУЛЯ
# --- ФАЙЛ: dino_erp_stock/__manifest__.py
#

{
    'name': 'Dino ERP Stock',
    'version': '2.0',
    'summary': 'Custom Component & Nomenclature Management',
    'author': 'Stepan',
    'category': 'Manufacturing',
'depends': [
        'base',      # Ядро системы, права пользователей, image.mixin
        'mail',      # Чаттер, сообщения, активности
        'uom',       # Единицы измерения (шт, кг, м)
        'product',   # Категорий товаров (product.category)
        'stock',     # Склад (для меню и будущей интеграции остатков)
        'mrp',       # Производство (пусть будет для совместимости меню)
    ],
    'data': [
        # 1. Права доступа (Всегда первыми)
        'security/ir.model.access.csv',
        
        # 2. Системные данные (Авто-нумерация артикулов)
        'data/ir_sequence_data.xml',
        
        # 3. Интерфейс (Views)
        'views/dino_component_views.xml',    # Меню и формы Семейств
        'views/dino_nomenclature_views.xml', # Меню и формы Номенклатуры
        'views/dino_nomenclature_quick_create.xml', # Упрощенная форма создания
        'views/dino_component_category_views.xml', # <-Форма категорий
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}