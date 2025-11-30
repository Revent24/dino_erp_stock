#
# --- /dino_erp_stock/__manifest__.py ---
#

{
    'name': "Dino ERP Stock: Динамические производство",
    'summary': "Модуль для внедрения логики 'Склада' из презентации.",
    # ... остальные метаданные ...
    'version': '1.0',

    # ЗАВИСИМОСТИ
    'depends': [
        'base', # база
        'stock', # склад
        'mrp', # управление запасами
        'mail',  # обсуждение
        'uom'
    ],

    # Файлы, которые будут загружены в базу при установке. Порядок важен!
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/product_component_views.xml',    # <-- Компоненты
        'views/product_attribute_views.xml',    # <-- Атрибуты
        'views/product_component_bom_views.xml', # <-- Спецификации
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}