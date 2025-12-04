# --- ИНИЦИАЛИЗАЦИЯ МОДЕЛЕЙ
# --- ФАЙЛ: dino_erp_stock/models/__init__.py
#

from . import dino_component      # 1. Семейства (Родители)
from . import dino_nomenclature   # 2. Номенклатура (Исполнения/Товары)
from . import dino_parameter      # 3. Технические параметры
from . import dino_bom            # 4. Строки спецификации (BOM)
from . import dino_component_category  # Разширение для категории