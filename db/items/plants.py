from utils.datamgr import Item
from db.itemtags import Tag

ITEMS = (
    Item('rice_plant', '벼', '쌀이 열려 있는 벼이다.', 100, '🌾', tags=[Tag.Plant], selling=20),
    Item('wheat', '밀', '밀알이 풍성하게 맺혀 있는 밀이다.', 100, '🌾', tags=[Tag.Plant], selling=12),
    Item('rice_seeds', '볍씨', '벼를 심기 위한 벼의 씨이다.', 100, '🌾', tags=[Tag.Seed], meta={'plantable': True, 'farm_plant': 'rice'}, selling=20),
    Item('rice', '쌀', '신선한 하얀 쌀이다.', 100, '🥚', tags=[Tag.Food], selling=8),
    Item('wheat_seeds', '밀 씨앗', '밀알에서 골라낸 밀의 씨앗이다.', 100, '🥚', tags=[Tag.Seed], meta={'plantable': True, 'farm_plant': 'wheat'}, selling=5),
    Item('flour', '밀가루', '밀을 빻아 만든 밀가루이다.', 100, '🥛', tags=[Tag.Etc], selling=30),
)