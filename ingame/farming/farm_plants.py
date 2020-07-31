from utils.gamemgr import FarmPlant
from utils.gamemgr import FarmPlantStatus as st

PLANTS = (
    FarmPlant('rice', '벼', 'rice_plant', (5, 10), growtime={st.Planted: (9000, 11000), st.Sprouted: (18000, 22000), st.Growing: (12000, 14200), st.AllGrownUp: None}),
    FarmPlant('wheat', '밀', 'wheat', (7, 12), growtime={st.Planted: (6000, 8000), st.Sprouted: (12000, 16000), st.Growing: (8000, 10000), st.AllGrownUp: None}),
)