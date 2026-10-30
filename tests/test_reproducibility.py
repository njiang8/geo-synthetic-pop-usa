"""Same seed -> byte-identical outputs; different seed -> different outputs.

Runs the real synthesis and network drivers on a synthetic 3-tract Utah fixture
(DP1-style tract rows, roads, OD, workplaces, schools, daycares, urban polygon).
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import LineString, Point, box

ROOT = Path(__file__).resolve().parent.parent
SYNTH = ROOT / 'code' / '1-population-synthesis' / 'run-synthesis-by-state.py'
EDU_HHOLD = ROOT / 'code' / '2-social-networks' / 'create_edu_hhold_get_work_pop.py'
WORK = ROOT / 'code' / '2-social-networks' / 'create_work_networks.py'

CRS = 'EPSG:4269'
TRACTS = ['49035000100', '49035000200', '49035000300']
X0, Y0, SIZE = -111.90, 40.70, 0.01  # tract i is the box [X0 + i*SIZE, X0 + (i+1)*SIZE] x [Y0, Y0 + SIZE]
RUN = 'ut_c035'

# 13 columns must precede DP1_0026C: __create_individuals__ reads the age-sex
# groups positionally as tract[13:50] (minus DP1_0049C).
LEAD_COLS = ['DP1_0001C', 'DP1_0025C', 'WP_CNT'] + [f'DP1_{i:04d}C' for i in range(2, 12)]
MALE_AGE = [f'DP1_{i:04d}C' for i in range(26, 44)]    # 18 five-year groups
FEMALE_AGE = [f'DP1_{i:04d}C' for i in range(50, 68)]  # 18 five-year groups
PER_GROUP = 3
HHOLD = {  # 30 households: types 0..10 = 6,6,1,1,2,1,1,2,2,2,6
    'DP1_0125C': 2, 'DP1_0127C': 0, 'DP1_0128C': 0, 'DP1_0130C': 1, 'DP1_0131C': 1,
    'DP1_0132C': 30, 'DP1_0133C': 12, 'DP1_0134C': 6, 'DP1_0135C': 2, 'DP1_0136C': 1,
    'DP1_0137C': 6, 'DP1_0138C': 3, 'DP1_0139C': 1, 'DP1_0140C': 1,
    'DP1_0141C': 10, 'DP1_0142C': 4, 'DP1_0143C': 2, 'DP1_0144C': 2,
}


def _tract_box(i):
    return box(X0 + i * SIZE, Y0, X0 + (i + 1) * SIZE, Y0 + SIZE)


def _write_fixture(data_dir):
    proc = data_dir / 'processed-data'
    for sub in ('census', 'od', 'road', 'edu', 'urban'):
        (proc / sub).mkdir(parents=True)

    # tracts
    rows = []
    for geoid in TRACTS:
        row = {'GEOID': geoid}
        row.update({c: 0 for c in LEAD_COLS})
        row['DP1_0001C'] = PER_GROUP * 36
        row['DP1_0025C'] = PER_GROUP * 18
        row['WP_CNT'] = 5
        row.update({c: PER_GROUP for c in MALE_AGE})
        row['DP1_0049C'] = PER_GROUP * 18
        row.update({c: PER_GROUP for c in FEMALE_AGE})
        row.update(HHOLD)
        rows.append(row)
    tracts = gpd.GeoDataFrame(rows, geometry=[_tract_box(i) for i in range(len(TRACTS))], crs=CRS)
    tracts.to_file(proc / 'census' / 'ut-tracts-demo-work.shp.zip', driver='ESRI Shapefile')

    # roads: local (S1400) streets for homes, one secondary (S1200) road for workplaces
    lines, mtfcc = [], []
    for i in range(len(TRACTS)):
        x_lo, x_hi = X0 + i * SIZE + 0.001, X0 + (i + 1) * SIZE - 0.001
        for k in range(1, 4):
            y = Y0 + k * SIZE / 4
            lines.append(LineString([(x_lo, y), (x_hi, y)]))
            mtfcc.append('S1400')
        x = X0 + (i + 0.5) * SIZE
        lines.append(LineString([(x, Y0 + 0.001), (x, Y0 + SIZE - 0.001)]))
        mtfcc.append('S1200')
    gpd.GeoDataFrame({'MTFCC': mtfcc}, geometry=lines, crs=CRS).to_file(
        proc / 'road' / 'UT_road_cleaned.shp.zip', driver='ESRI Shapefile')

    # commuting: every tract sends 10 workers to each tract
    pd.DataFrame([{'home': h, 'work': w, 'S000': 10} for h in TRACTS for w in TRACTS]).to_csv(
        proc / 'od' / 'ut-tract-od-2020.csv', index=False)
    with open(proc / 'us_tract_number_work.json', 'w') as f:
        for geoid in TRACTS:
            f.write(json.dumps({'GEOID': geoid, 'WP_CNT': 5, 'WP_PROBA': [0.1, 0.15, 0.2, 0.25, 0.3]}) + '\n')

    # education sites: two schools (5-17) and two daycares (0-4) per tract
    def sites(prefix, s_age, e_age):
        recs, pts = [], []
        for i in range(len(TRACTS)):
            for k, dx in enumerate((0.3, 0.7)):
                x, y = X0 + (i + dx) * SIZE, Y0 + 0.5 * SIZE
                recs.append({'eduID': f'{TRACTS[i]}{prefix}{k}', 'LATITUDE': y, 'LONGITUDE': x,
                             's_age': s_age, 'e_age': e_age, 'count': 0, 'ENROLLMENT': 100})
                pts.append(Point(x, y))
        return gpd.GeoDataFrame(recs, geometry=pts, crs=CRS)
    sites('s', 5, 17).to_file(proc / 'edu' / 'ut_school_id.gpkg', driver='GPKG')
    sites('d', 0, 4).to_file(proc / 'edu' / 'ut_daycare_id.gpkg', driver='GPKG')

    # urban area: the western half of the fixture
    gpd.GeoDataFrame(geometry=[box(X0, Y0, X0 + 1.5 * SIZE, Y0 + SIZE)], crs=CRS).to_file(
        proc / 'urban' / 'UT_urban.gpkg', driver='GPKG')


def _run(script, data_dir, *args):
    env = dict(os.environ, GSPN_DATA_DIR=str(data_dir),
               PYTHONPATH=os.pathsep.join([str(ROOT), os.environ.get('PYTHONPATH', '')]))
    env.pop('OGR_CURRENT_DATE', None)  # the synthesis driver must pin GeoPackage timestamps itself
    result = subprocess.run([sys.executable, str(script), '--state', 'ut', '--counties', '035', *args],
                            cwd=script.parent, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr[-3000:]


def _pipeline(data_dir, seed):
    """Synthesis, then education/household networks, then the work network; returns {relpath: bytes}."""
    _write_fixture(data_dir)
    _run(SYNTH, data_dir, '--seed', str(seed))
    results = data_dir / 'results-data'
    state_dir = results / 'ut'
    assert not (state_dir / f'{RUN}_error_log.csv').exists(), (state_dir / f'{RUN}_error_log.csv').read_text()
    timing = pd.read_csv(state_dir / f'{RUN}_timing.csv', dtype={'tract': str})
    totals = timing[timing.scope == 'tract_total']
    assert set(totals.tract) == set(TRACTS)
    assert (totals.status == 'success').all()
    assert (timing.elapsed_seconds >= 0).all()
    for tract in TRACTS:
        stages = timing[(timing.tract == tract) & (timing.scope == 'tract_stage')]
        assert set(stages.stage) == {
            'education snapshot', 'individual creation', 'household assignment', 'home placement',
            'job assignment', 'workplace placement', 'education assignment', 'urban classification',
            'verification'}
        assert stages.elapsed_seconds.sum() <= totals.loc[totals.tract == tract, 'elapsed_seconds'].iloc[0]
    assert {'load roads', 'synthesis loop', 'collect population', 'write population GeoPackage',
            'state total'} <= set(timing.stage)

    # the network driver reads a pickle the synthesis driver does not yet write (Agent B's hand-off fix)
    pop = gpd.read_file(state_dir / f'{RUN}_population.gpkg')
    assert set(pop['id'].str[:11]) == set(TRACTS)
    pop.to_pickle(state_dir / f'{RUN}_population.pickle')
    (results / '1-us').mkdir(exist_ok=True)
    _run(EDU_HHOLD, data_dir, '--seed', str(seed))
    _run(WORK, data_dir, '--seed', str(seed))

    outputs = {}
    for path in sorted(results.rglob('*')):
        if (path.is_file() and path.suffix != '.pickle'
                and not path.name.endswith(('_timing.csv', '_timing_summary.csv'))):
            outputs[str(path.relative_to(results))] = path.read_bytes()
    return outputs


@pytest.fixture(scope='module')
def runs(tmp_path_factory):
    return {name: _pipeline(tmp_path_factory.mktemp(name), seed)
            for name, seed in (('a', 42), ('b', 42), ('c', 7))}


EXPECTED = [f'ut/{RUN}_population.gpkg', f'ut/{RUN}_workplace.gpkg', f'ut/{RUN}_verification.csv',
            f'ut/social_networks/{RUN}_household_network.csv',
            f'ut/social_networks/{RUN}_school_network.csv',
            f'ut/social_networks/{RUN}_daycare_network.csv',
            f'1-us/{RUN}_work_population.csv', f'1-us/{RUN}_work_network.csv']


def test_expected_outputs_written(runs):
    for name in EXPECTED:
        assert name in runs['a'], name
        assert len(runs['a'][name]) > 0, name


def test_same_seed_byte_identical(runs):
    assert runs['a'].keys() == runs['b'].keys()
    differing = [k for k in runs['a'] if runs['a'][k] != runs['b'][k]]
    assert differing == []


def test_different_seed_differs(runs):
    for name in [f'ut/{RUN}_population.gpkg', f'ut/{RUN}_workplace.gpkg',
                 f'ut/social_networks/{RUN}_household_network.csv', f'1-us/{RUN}_work_network.csv']:
        assert runs['a'][name] != runs['c'][name], name


def test_network_seed_alone_changes_ties():
    """With the population fixed, only the NWS draw depends on the network seed."""
    from src.create_social_networks import create_network
    people = pd.DataFrame({'wp': ['w1'] * 30}, index=[f'p{i}' for i in range(30)])
    g1 = create_network(people, 'Work', seed=1)
    g2 = create_network(people, 'Work', seed=1)
    g3 = create_network(people, 'Work', seed=2)
    assert sorted(map(sorted, g1.edges())) == sorted(map(sorted, g2.edges()))
    assert sorted(map(sorted, g1.edges())) != sorted(map(sorted, g3.edges()))
    # NWS(n, 4, 0.3) keeps the ring lattice: every node has degree >= 4
    assert min(dict(g1.degree()).values()) >= 4


def test_unseeded_steps_keep_global_fallback():
    """Callers that pass no rng still work (legacy global np.random / fixed shuffle)."""
    from src.assign_workplace import generate_workplace_id
    work = pd.DataFrame({'WP_CNT': [3], 'WP_PROBA': [np.array([0.2, 0.3, 0.5])]}, index=['49035000100'])
    assert generate_workplace_id('49035000100', work).startswith('49035000100w')
    rng_a, rng_b = np.random.default_rng(5), np.random.default_rng(5)
    assert generate_workplace_id('49035000100', work, rng_a) == generate_workplace_id('49035000100', work, rng_b)


def test_wp_proba_seeded():
    from src.tools import wp_proba
    a = wp_proba(6, np.random.default_rng(3))
    assert np.array_equal(a, wp_proba(6, np.random.default_rng(3)))
    assert not np.array_equal(a, wp_proba(6, np.random.default_rng(4)))
    assert len(wp_proba(6)) == 6 and np.isclose(a.sum(), 1)
