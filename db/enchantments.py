from utils.datamgr import Enchantment, EnchantType

ENCHANTMENTS = (
    Enchantment('long-battery', '긴 배터리', 4, EnchantType.Passive, price_percent=1.2),
    Enchantment('case', '케이스', 1, EnchantType.Passive, price_percent=1.05),
    Enchantment('ram', '램', 4, EnchantType.Passive, price_percent=1.05),
)