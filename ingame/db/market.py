from exts.utils.datamgr import MarketItem, ItemData, EnchantmentData

MARKET = (
    MarketItem(ItemData('galaxy_zflip', 1, []), price=10000, discount=9000),
    MarketItem(ItemData('galaxy_zflip', 1, [EnchantmentData('long-battery', 2)]), price=12000, discount=11500),
)