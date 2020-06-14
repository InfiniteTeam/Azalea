from exts.utils.datamgr import MarketItem, ItemData, EnchantmentData

MARKET = (
    MarketItem(ItemData(0, 1, []), 10000, 8000, 9000),
    MarketItem(ItemData(0, 1, [EnchantmentData('long=battery', 2)]), 12000, 10000, 11500),
)
