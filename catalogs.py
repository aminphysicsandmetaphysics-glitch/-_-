"""Reference catalogs that let the audit engine auto-fill technical values
instead of requiring the end user to know them.

Two catalogs are provided:

1. ``ENVELOPE_CATALOG`` -- typical steady-state heat transfer coefficients
   (U-values, W/m2.K) for construction types common in Iranian residential
   buildings. A homeowner or a level-1 auditor rarely knows the U-value of
   their wall, but they can identify the construction type from a short
   list ("double-wythe brick, no insulation", "AAC block with insulation",
   ...). Values below are typical reference-grade figures consistent with
   general building-science practice (ASHRAE Fundamentals-class ranges) and
   are meant for preliminary / Level 1-2 audits. They are intentionally
   editable per-building (``Building.envelope_overrides``) because a real
   مبحث ۱۹ compliance calculation requires project-specific certified
   values.

2. ``EQUIPMENT_CATALOG`` -- typical rated power / consumption for common
   household equipment classes, so a user can pick "کولر گازی اینورتر --
   ۱۸۰۰۰ (۲ تن)" from a dropdown and get a sane default power draw and
   duty cycle instead of typing raw watts.

Both catalogs are data, not code -- extending them means adding an entry,
never touching the calculation engine.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EnvelopeMaterial:
    key: str
    category: str  # wall | roof | floor | window
    label_fa: str
    label_en: str
    u_value: float  # W/m2.K
    insulated: bool
    notes_fa: str = ""


ENVELOPE_CATALOG: list[EnvelopeMaterial] = [
    # --- Walls ---
    EnvelopeMaterial("wall_brick_single_wythe", "wall", "دیوار آجری یک‌ضخامته بدون عایق", "Single-wythe brick, uninsulated", 1.9, False,
                      "معمول در بناهای قدیمی، بدون لایه عایق حرارتی"),
    EnvelopeMaterial("wall_brick_double_wythe", "wall", "دیوار آجری دوجداره بدون عایق", "Double-wythe brick cavity wall, uninsulated", 1.25, False),
    EnvelopeMaterial("wall_brick_double_wythe_insulated", "wall", "دیوار آجری دوجداره با عایق ۵ سانتی", "Double-wythe brick with 5cm insulation", 0.5, True),
    EnvelopeMaterial("wall_aac_block", "wall", "بلوک هبلکس/سبک بدون عایق اضافه", "AAC (autoclaved aerated concrete) block, uninsulated", 0.8, False),
    EnvelopeMaterial("wall_aac_block_insulated", "wall", "بلوک هبلکس با عایق اضافه", "AAC block with added insulation", 0.4, True),
    EnvelopeMaterial("wall_concrete_uninsulated", "wall", "دیوار بتنی بدون عایق", "Bare concrete/shear wall, uninsulated", 2.4, False),
    # --- Roofs ---
    EnvelopeMaterial("roof_flat_uninsulated", "roof", "پشت‌بام تخت بدون عایق (قیرگونی معمولی)", "Flat bituminous roof, uninsulated", 2.2, False),
    EnvelopeMaterial("roof_flat_insulated", "roof", "پشت‌بام تخت با عایق پلی‌استایرن ۵ سانتی", "Flat roof with 5cm EPS/XPS insulation", 0.45, True),
    EnvelopeMaterial("roof_pitched_uninsulated", "roof", "سقف شیبدار بدون عایق", "Pitched roof, uninsulated", 1.6, False),
    EnvelopeMaterial("roof_pitched_insulated", "roof", "سقف شیبدار با عایق پشم‌سنگ/پشم‌شیشه", "Pitched roof with mineral-wool insulation", 0.35, True),
    # --- Floors / slab-on-grade (heat loss to unheated space or ground) ---
    EnvelopeMaterial("floor_slab_on_grade", "floor", "کف در تماس با زمین بدون عایق", "Uninsulated slab-on-grade", 0.9, False),
    EnvelopeMaterial("floor_slab_on_grade_insulated", "floor", "کف در تماس با زمین با عایق", "Insulated slab-on-grade", 0.4, True),
    EnvelopeMaterial("floor_over_unheated", "floor", "کف بالای فضای سرد/پارکینگ", "Floor over unheated space (parking, basement)", 1.2, False),
    # --- Windows ---
    EnvelopeMaterial("window_single_aluminum", "window", "پنجره تک‌جداره با قاب آلومینیومی", "Single glazing, aluminum frame (no thermal break)", 5.8, False),
    EnvelopeMaterial("window_single_upvc", "window", "پنجره تک‌جداره با قاب UPVC/چوبی", "Single glazing, uPVC/wood frame", 4.7, False),
    EnvelopeMaterial("window_double_aluminum", "window", "پنجره دوجداره معمولی با قاب آلومینیومی", "Standard double glazing, aluminum frame", 3.0, True),
    EnvelopeMaterial("window_double_lowe_upvc", "window", "پنجره دوجداره کم‌گسیل (Low-E) با قاب ترمال‌بریک/UPVC", "Low-E double glazing, thermal-break/uPVC frame", 1.8, True),
    EnvelopeMaterial("window_double_lowe_argon", "window", "پنجره دوجداره کم‌گسیل با گاز آرگون", "Low-E argon-filled double glazing, high performance", 1.2, True),
]


def get_envelope_options(category: str | None = None) -> list[dict]:
    items = ENVELOPE_CATALOG if category is None else [m for m in ENVELOPE_CATALOG if m.category == category]
    return [
        {
            "key": m.key,
            "category": m.category,
            "label_fa": m.label_fa,
            "label_en": m.label_en,
            "u_value": m.u_value,
            "insulated": m.insulated,
            "notes_fa": m.notes_fa,
        }
        for m in items
    ]


def get_u_value(key: str | None, default: float) -> float:
    if not key:
        return default
    for material in ENVELOPE_CATALOG:
        if material.key == key:
            return material.u_value
    return default


@dataclass(frozen=True)
class EquipmentPreset:
    key: str
    fuel: str  # electric | gas
    category: str
    label_fa: str
    label_en: str
    typical_power_w: float = 0.0          # electric appliances
    typical_gas_m3_per_hour: float = 0.0  # gas appliances
    typical_hours_per_day: float = 0.0
    typical_days_per_year: float = 365
    efficiency_note_fa: str = ""


EQUIPMENT_CATALOG: list[EquipmentPreset] = [
    # --- Electric ---
    EquipmentPreset("ac_split_9000_inverter", "electric", "cooling", "کولر گازی اینورتر ۹۰۰۰ (۱ تن)", "Inverter split AC 9,000 BTU", 900, typical_hours_per_day=6, typical_days_per_year=120),
    EquipmentPreset("ac_split_12000_inverter", "electric", "cooling", "کولر گازی اینورتر ۱۲۰۰۰ (۱.۵ تن)", "Inverter split AC 12,000 BTU", 1250, typical_hours_per_day=6, typical_days_per_year=120),
    EquipmentPreset("ac_split_18000_inverter", "electric", "cooling", "کولر گازی اینورتر ۱۸۰۰۰ (۲ تن)", "Inverter split AC 18,000 BTU", 1800, typical_hours_per_day=6, typical_days_per_year=120),
    EquipmentPreset("ac_split_18000_fixed", "electric", "cooling", "کولر گازی معمولی (غیر اینورتر) ۱۸۰۰۰", "Fixed-speed split AC 18,000 BTU", 2400, typical_hours_per_day=6, typical_days_per_year=120,
                     efficiency_note_fa="مصرف حدود ۳۰-۴۰٪ بیشتر از نوع اینورتر با ظرفیت مشابه"),
    EquipmentPreset("cooler_evaporative", "electric", "cooling", "کولر آبی", "Evaporative (swamp) cooler", 750, typical_hours_per_day=8, typical_days_per_year=120),
    EquipmentPreset("fridge_a_plus", "electric", "refrigeration", "یخچال‌فریزر رده انرژی A+ و بالاتر", "Refrigerator, energy class A+ or better", 60, typical_hours_per_day=24, typical_days_per_year=365),
    EquipmentPreset("fridge_old_no_label", "electric", "refrigeration", "یخچال‌فریزر قدیمی بدون برچسب انرژی", "Older refrigerator, no energy label", 160, typical_hours_per_day=24, typical_days_per_year=365,
                     efficiency_note_fa="یخچال‌های قدیمی معمولاً ۲ تا ۳ برابر رده A مصرف دارند"),
    EquipmentPreset("led_lighting_avg_home", "electric", "lighting", "روشنایی LED (میانگین کل واحد مسکونی)", "LED lighting, whole-home average", 80, typical_hours_per_day=5, typical_days_per_year=365),
    EquipmentPreset("incandescent_lighting_avg_home", "electric", "lighting", "روشنایی لامپ رشته‌ای/هالوژن (میانگین کل واحد)", "Incandescent/halogen lighting, whole-home average", 350, typical_hours_per_day=5, typical_days_per_year=365),
    EquipmentPreset("washing_machine", "electric", "appliance", "ماشین لباسشویی", "Washing machine", 500, typical_hours_per_day=1, typical_days_per_year=150),
    EquipmentPreset("tv_led_43", "electric", "electronics", "تلویزیون LED ۴۳ اینچ", "43-inch LED television", 70, typical_hours_per_day=4, typical_days_per_year=365),
    EquipmentPreset("electric_water_heater", "electric", "water_heating", "آبگرمکن برقی", "Electric water heater", 2000, typical_hours_per_day=2, typical_days_per_year=365),
    # --- Gas ---
    EquipmentPreset("gas_wall_heater_old", "gas", "heating", "بخاری گازی دیواری قدیمی", "Older gas wall heater", typical_gas_m3_per_hour=0.9, typical_hours_per_day=8, typical_days_per_year=150),
    EquipmentPreset("gas_boiler_condensing", "gas", "heating", "پکیج گازی چگالشی پرراندمان", "Condensing gas boiler (high efficiency)", typical_gas_m3_per_hour=1.1, typical_hours_per_day=6, typical_days_per_year=150,
                     efficiency_note_fa="راندمان بالاتر نسبت به پکیج معمولی، مصرف کمتر برای همان گرمایش"),
    EquipmentPreset("gas_boiler_standard", "gas", "heating", "پکیج گازی معمولی", "Standard (non-condensing) gas boiler", typical_gas_m3_per_hour=1.5, typical_hours_per_day=6, typical_days_per_year=150),
    EquipmentPreset("gas_water_heater_tank", "gas", "water_heating", "آبگرمکن گازی مخزن‌دار", "Gas storage water heater", typical_gas_m3_per_hour=0.35, typical_hours_per_day=4, typical_days_per_year=365),
    EquipmentPreset("gas_water_heater_instant", "gas", "water_heating", "آبگرمکن گازی دیواری (فوری)", "Instantaneous gas water heater", typical_gas_m3_per_hour=0.5, typical_hours_per_day=2, typical_days_per_year=365),
    EquipmentPreset("gas_stove", "gas", "cooking", "اجاق گاز", "Gas stove/cooktop", typical_gas_m3_per_hour=0.2, typical_hours_per_day=1.5, typical_days_per_year=365),
]


def get_equipment_options(fuel: str | None = None) -> list[dict]:
    items = EQUIPMENT_CATALOG if fuel is None else [e for e in EQUIPMENT_CATALOG if e.fuel == fuel]
    return [
        {
            "key": e.key,
            "fuel": e.fuel,
            "category": e.category,
            "label_fa": e.label_fa,
            "label_en": e.label_en,
            "typical_power_w": e.typical_power_w,
            "typical_gas_m3_per_hour": e.typical_gas_m3_per_hour,
            "typical_hours_per_day": e.typical_hours_per_day,
            "typical_days_per_year": e.typical_days_per_year,
            "efficiency_note_fa": e.efficiency_note_fa,
        }
        for e in items
    ]


def get_equipment_preset(key: str) -> EquipmentPreset | None:
    for item in EQUIPMENT_CATALOG:
        if item.key == key:
            return item
    return None
