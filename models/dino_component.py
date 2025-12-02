# --- МОДЕЛЬ: КОМПОНЕНТ (СЕМЕЙСТВО / РОДИТЕЛЬ)
# --- ФАЙЛ: models/dino_component.py
#

from odoo import fields, models, _, api

class DinoComponent(models.Model):
    _name = 'dino.component'
    _description = 'Component Family'
    _inherit = ['image.mixin', 'mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(default=True)
    name = fields.Char(string=_('Family Name'), required=True, translate=True, tracking=True)
    category_id = fields.Many2one('product.category', string=_('Category'), tracking=True)
    uom_id = fields.Many2one(
        'uom.uom', 
        string=_('Unit of Measure'), 
        required=True,
        default=lambda self: self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
    )
    nomenclature_ids = fields.One2many('dino.nomenclature', 'component_id', string=_('Nomenclatures'))
    
    # ЗАМЕТКИ
    description = fields.Html(string=_('Internal Notes'), translate=True)
    is_favorite = fields.Boolean(string=_('Favorite'))

    # === НОВОЕ: ПОДСЧЕТ И КНОПКА ===
    nomenclature_count = fields.Integer(compute='_compute_nomenclature_count')

    def _compute_nomenclature_count(self):
        for rec in self:
            rec.nomenclature_count = len(rec.nomenclature_ids)

    def action_view_nomenclatures(self):
        self.ensure_one()
        return {
            'name': _('Nomenclatures'),
            'type': 'ir.actions.act_window',
            'res_model': 'dino.nomenclature',
            'view_mode': 'list,form',
            'domain': [('component_id', '=', self.id)],
            'context': {'default_component_id': self.id}, 
        }
    # ===============================

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Component Family name must be unique!'),
    ]

    def toggle_is_favorite(self):
        for rec in self:
            rec.is_favorite = not rec.is_favorite

# --- END ---