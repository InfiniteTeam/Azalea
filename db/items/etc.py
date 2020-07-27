from utils.datamgr import Item
from db.itemtags import Tag

ITEMS = (
    Item('galaxy_zflip', '갤럭시 Z플립', '모 회사의 폴더블 스마트폰이다.', 100, '📱', tags=[Tag.Phone], enchantments=['long-battery'], selling=8000),
    Item('odroid_n2', 'ODROID N2', '오드로이드 N2.', 100, '⚙'),
    Item('buldak', '불닭볶음면', '개맛있다.', 100, '🍜'),
    Item('nad', '니코틴아마이드아데닌다이뉴클레오타이드', '길다.', 100, '🧬'),
    Item('crucian_carp', '붕어', '그냥 흔한 붕어다.', 100, '🐟', tags=[Tag.Fish], meta={'catchable': True, 'percentage': 2, 'exp_multiple': 1}, selling=4000),
    Item('carp', '잉어', '뭐라할 거 없이 그냥 잉어.', 100, '🐟', tags=[Tag.Fish], meta={'catchable': True, 'percentage': 1.5, 'exp_multiple': 1.1}, selling=6000),
    Item('salmon', '연어', '몸의 색이 붉은 연어다. 개발자 알파가 생선회 중 가장 좋아하는 거라고 한다.', 100, '🐟', tags=[Tag.Fish], meta={'catchable': True, 'percentage': 1.2, 'exp_multiple': 1.3}, selling=8000),
    Item('tuna', '참치', '엄청 크다.', 100, '🐟', tags=[Tag.Fish], meta={'catchable': True, 'percentage': 1, 'exp_multiple': 1.5}, selling=12000),
    Item('common_fishing_rod', '평범한 낚싯대', '나뭇가지로 만든 낚싯대이다.', 100, '🎣', tags=[Tag.FishingRod], meta={'luck': 1.2}, selling=800),
    Item('wooden_pickaxe', '평범한 나무 곡괭이', '그저 평범한 나무로 만든 곡괭이다.', 100, '⛏', tags=[Tag.Pickaxe], selling=800),
)