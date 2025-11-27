# -*- coding: utf-8 -*-
#
# -----  МОДУЛЬ СКЛАД -----
# --- dino_erp_stock/models/product_template.py ---

from odoo import models, fields, api
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # --- СВЯЗЬ С ПРОИСХОЖДЕНИЕМ (УСТРАНЕНИЕ KEYERROR) ---
    
    # НОВОЕ RELATED ПОЛЕ. Ссылается на related-поле в product.category,
    # которое берет код из product.origin.type.
    dino_origin_type_code = fields.Char(
        related='categ_id.dino_origin_type_code', 
        string="Технический код происхождения",
        readonly=True,
        store=True,
        help="Технический код происхождения, необходимый для логики."
    )
    
    # --- НОВЫЕ ПОЛЯ ДЛЯ ЦЕНООБРАЗОВАНИЯ И ЗАПАСОВ ---
    
    calculated_cost_incl_tax = fields.Float(
        string="Расчетная себестоимость с НДС",
        digits='Product Price',
        compute='_compute_cost_fields',
        store=True,
        help="Расчетная себестоимость с учетом НДС (зависит от настроек Категории)."
    )
    
    dino_markup_type = fields.Selection([
        ('percent', 'Процент'),
        ('amount', 'Фиксированная сумма'),
        ('none', 'Не применять'),
    ],
        string="Тип надбавки",
        default='none',
        required=True,
        help="Определяет, как будет рассчитываться надбавка к себестоимости."
    )
    
    dino_markup_percent = fields.Float(
        string="Надбавка (%)",
        digits=(6, 2),
    )
    
    dino_markup_amount = fields.Float(
        string="Надбавка (Сумма)",
        digits='Product Price',
    )
    
    min_order_qty = fields.Float(
        string="Минимальный заказ (Dino)",
        help="Минимальное количество, которое необходимо закупить/произвести для восполнения запаса.",
    )

    # --- СУЩЕСТВУЮЩИЕ ПОЛЯ И ЛОГИКА ---
    
    calculated_cost = fields.Float(
        string="Расчетная себестоимость (BOM)",
        digits='Product Price',
        compute='_compute_cost_fields',
        store=True,
        help="Расчетная себестоимость на основе данных Спецификации (BOM). (Пока плоская логика)."
    )
    
    actual_cost = fields.Float(
        string="Фактическая себестоимость",
        digits='Product Price',
        help="Фактическая себестоимость, полученная из производственных заказов."
    )
    
    min_qty = fields.Float(
        string="Неснижаемый остаток (Dino)",
        help="Минимальное количество, включая аналоги, ниже которого генерируется запрос на закупку.",
    )
    
    qty_available_with_analogs = fields.Float(
        string="Доступно (с Аналогами)",
        compute='_compute_qty_with_analogs',
        store=True,
        digits='Product Unit of Measure',
        help="Суммарное количество в наличии (Qty Available) основного товара и всех его утвержденных аналогов."
    )
    
    purchase_required = fields.Boolean(
        string="Требуется закупка (Dino)",
        compute='_compute_purchase_required',
        store=True,
        search='_search_purchase_required',
        help="Отмечено, если суммарный запас (с аналогами) ниже неснижаемого остатка."
    )

    apply_analogs = fields.Boolean(
        string="Применить аналоги",
        default=False,
        help="Отметьте, если для этого товара может быть утвержден список аналогов."
    )
    
    analog_ids = fields.Many2many(
        'product.template',
        'product_template_analog_rel',
        'template_id',
        'analog_id',
        string="Аналогичные товары",
        domain="['&', ('categ_id', '=', categ_id), ('apply_analogs', '=', False)]",
        help="Список товаров, которые могут быть использованы как аналоги."
    )

    # ----------------------------------------------------------------------------------------
    # ЛОГИКА РАСЧЕТА ЗАПАСОВ С АНАЛОГАМИ
    # ----------------------------------------------------------------------------------------
    
    @api.depends('qty_available', 'analog_ids.qty_available')
    def _compute_qty_with_analogs(self):
        # ... (логика без изменений)
        for product in self:
            total_qty = product.qty_available
            for analog in product.analog_ids:
                total_qty += analog.qty_available
            product.qty_available_with_analogs = total_qty

    # ----------------------------------------------------------------------------------------
    # ЛОГИКА КОНТРОЛЯ ЗАКУПОК
    # ----------------------------------------------------------------------------------------

    @api.depends('min_qty', 'qty_available_with_analogs')
    def _compute_purchase_required(self):
        # ... (логика без изменений)
        for product in self:
            if product.apply_analogs and product.min_qty > 0:
                product.purchase_required = product.qty_available_with_analogs < product.min_qty
            else:
                product.purchase_required = False

    def _search_purchase_required(self, operator, value):
        # ... (заглушка без изменений)
        return [(0, '=', 1)] 
            
    # ----------------------------------------------------------------------------------------
    # ЛОГИКА РАСЧЕТА СЕБЕСТОИМОСТИ (ПЛОСКАЯ ЛОГИКА)
    # ----------------------------------------------------------------------------------------
    
    @api.depends('bom_ids', 'bom_ids.bom_line_ids.product_id.standard_price', 'categ_id.dino_origin_type_code')
    def _compute_cost_fields(self):
        """Расчет себестоимости, теперь с учетом типа происхождения."""
        for product in self:
            cost = 0.0
            
            # 1. Расчет себестоимости по BOM (только для Manufactured)
            if product.dino_origin_type_code in ('subcontract', 'internal_assembly', 'finished_good'):
                if product.bom_ids:
                    cost = sum(
                        line.product_id.standard_price * line.product_qty
                        for bom in product.bom_ids
                        for line in bom.bom_line_ids
                    )
                
            # 2. Для Purchase/Kit/Service: используем стандартную цену
            elif product.dino_origin_type_code in ('purchase', 'kit_component', 'service'):
                 cost = product.standard_price
            
            # 3. Присвоение себестоимости без НДС
            product.calculated_cost = cost
            
            # 4. Расчет себестоимости с НДС (ПОКА ПРОСТОЕ ПРИСВОЕНИЕ БЕЗ ЛОГИКИ НДС)
            # Эту логику нужно будет уточнить (зависит от налоговой категории)
            product.calculated_cost_incl_tax = cost