from exts.utils.datamgr import MarketItem, ItemData, EnchantmentData

MARKET = (
    MarketItem(ItemData(0, 1, []), price=10000, selling=8000, discount=9000),
    MarketItem(ItemData(0, 1, [EnchantmentData('long-battery', 2)]), price=12000, selling=10000, discount=11500),
)