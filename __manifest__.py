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
    ],

    # Файлы, которые будут загружены в базу при установке. Порядок важен!
    'data': [
        'security/ir.model.access.csv',
        #'views/product_origin_type_views.xml',
        'views/product_component_views.xml'

    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}