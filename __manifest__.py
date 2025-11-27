#
# --- /dino_erp_stock/__manifest__.py ---
#

{
    'name': "Dino ERP Stock: Кастомный Склад",
    'summary': "Модуль для внедрения логики 'Склада' из презентации.",
    # ... остальные метаданные ...
    'version': '1.0',

    # ОСТАВЛЯЕМ ТОЛЬКО ЭТОТ ОДИН БЛОК ЗАВИСИМОСТЕЙ
    'depends': [
        'base', 
        'stock',
        'mrp', 
        'sale',
    ],

    # Файлы, которые будут загружены в базу при установке. Порядок важен!
    'data': [
        'security/ir.model.access.csv', 
        'views/product_origin_type_view.xml',
        'views/product_template_view.xml', 
        'views/product_category_view.xml',
        'views/product_template_action.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}