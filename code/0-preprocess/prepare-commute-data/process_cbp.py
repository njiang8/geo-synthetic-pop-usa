
import os
import pandas as pd
from loguru import logger
from src.settings import RAW_DATA_DIR, INTERIM_DATA_DIR

cbp_path = os.path.join(RAW_DATA_DIR, 'CBP2020.CB2000CBP_census/CBP2020.CB2000CBP-Data.csv')

cbp_df = pd.read_csv(cbp_path)
#cbp = pd.read_csv('../data/raw-data/CBP2020.CB2000CBP_census/CBP2020.CB2000CBP-Data.csv')#.iloc[1:,[0,9,11]]
cbp_df = cbp_df[(cbp_df['EMPSZES_LABEL'] == 'All establishments')
             & (cbp_df['NAICS2017'] == '00')].reset_index(drop=True).copy()
cbp_df['county'] = cbp_df.GEO_ID.astype(str).str[-5:]

logger.info(f"There are {len(cbp_df['county'].unique())} counties ")

campany_df = cbp_df.loc[:,['county', 'NAME', 'ESTAB']]

save_county_workplace_df_path = os.path.join(INTERIM_DATA_DIR, 'cbp/workplace_cbp.csv')

logger.info(f"Saving County Workplace df to {save_county_workplace_df_path}")
campany_df.to_csv(save_county_workplace_df_path)