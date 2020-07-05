from exts.utils.datamgr import Item

ITEMS = (
    Item(0, '갤럭시 Z플립', '모 회사의 폴더블 스마트폰이다.', 100, '📱', tags=['phone'], enchantments=['long-battery'], selling=8000),
    Item(1, 'ODROID N2', '오드로이드 N2.', 100, '⚙'),
    Item(2, '불닭볶음면', '개맛있다.', 100, '🍜'),
    Item(3, '니코틴아마이드아데닌다이뉴클레오타이드', '길다.', 100, '🧬'),
    Item(4, '붕어', '그냥 흔한 붕어다.', 100, '🐟', tags=['fishing'], meta={'percentage': 2}, selling=4000),
    Item(5, '잉어', '뭐라할 거 없이 그냥 잉어.', 100, '🐟', tags=['fishing'], meta={'percentage': 1.5}, selling=6000),
    Item(6, '연어', '몸의 색이 붉은 연어다. 개발자 알파가 생선회 중 가장 좋아하는 거라고 한다.', 100, '🐟', tags=['fishing'], meta={'percentage': 1.2}, selling=8000),
    Item(7, '참치', '엄청 크다.', 100, '🐟', tags=['fishing'], meta={'percentage': 1}, selling=12000),
)