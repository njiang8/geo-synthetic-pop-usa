import os
import subprocess
import sys
from pathlib import Path

import geopandas as gpd
from shapely.geometry import box

ROOT = Path(__file__).resolve().parent.parent
SYNTH = ROOT / 'code' / '1-population-synthesis' / 'run-synthesis-by-state.py'

# two Salt Lake (035) tracts, one Utah County (049) tract, one empty tract
TRACTS = {'49035100100': 10, '49035100200': 20, '49049000100': 30, '49035999999': 0}


def _write_fixture(data_dir):
    census = data_dir / 'processed-data' / 'census'
    census.mkdir(parents=True)
    gdf = gpd.GeoDataFrame(
        {'GEOID': list(TRACTS), 'DP1_0001C': list(TRACTS.values())},
        geometry=[box(i, 0, i + 1, 1) for i in range(len(TRACTS))], crs='EPSG:4269')
    gdf.to_file(census / 'ut-tracts-demo-work.shp.zip', driver='ESRI Shapefile')


def _dry_run(tmp_path, *args):
    _write_fixture(tmp_path)
    env = dict(os.environ, GSPN_DATA_DIR=str(tmp_path))
    return subprocess.run([sys.executable, str(SYNTH), '--dry-run', *args],
                          cwd=SYNTH.parent, env=env, capture_output=True, text=True)


def test_dry_run_one_county(tmp_path):
    result = _dry_run(tmp_path, '--state', 'ut', '--counties', '035')
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ['49035100100', '49035100200']
    assert not (tmp_path / 'results-data').exists()


def test_dry_run_whole_state(tmp_path):
    result = _dry_run(tmp_path, '--state', 'ut')
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ['49035100100', '49035100200', '49049000100']


def test_counties_without_state_rejected(tmp_path):
    result = _dry_run(tmp_path, '--counties', '035')
    assert result.returncode != 0
