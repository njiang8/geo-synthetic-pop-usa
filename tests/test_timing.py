import csv
import importlib.util
from pathlib import Path

import pytest

from src.timing import RunTiming


def test_averages_and_failed_tracts_are_separate(tmp_path):
    timing = RunTiming()
    for tract, elapsed, status in [('a', 2.0, 'success'), ('b', 4.0, 'success'), ('c', 9.0, 'failed')]:
        first = len(timing.rows)
        timing.rows.append(dict(scope='tract_stage', tract=tract, stage='households',
                                elapsed_seconds=elapsed, status='success', tract_status='success'))
        timing.finish_tract(first, tract, elapsed + 1, status)
    summary = {(r['scope'], r['status']): r for r in timing.summary()}
    assert summary['tract_stage', 'success']['count'] == 2
    assert summary['tract_stage', 'success']['total_seconds'] == 6
    assert summary['tract_stage', 'success']['mean_seconds'] == 3
    assert summary['tract_stage', 'success']['max_seconds'] == 4
    assert summary['tract_total', 'success']['mean_seconds'] == 4
    assert summary['tract_stage', 'failed']['mean_seconds'] == 9
    path = tmp_path / 'timing.csv'
    timing.report(path)
    with path.open() as stream:
        rows = list(csv.DictReader(stream))
    assert rows[-2]['status'] == 'success' and rows[-2]['tract_status'] == 'failed'
    with (tmp_path / 'timing_summary.csv').open() as stream:
        saved = list(csv.DictReader(stream))
    success = next(r for r in saved if r['scope'] == 'tract_stage' and r['status'] == 'success')
    assert float(success['mean_seconds']) == 3


def test_exception_is_recorded_and_propagated():
    timing = RunTiming()
    with pytest.raises(ValueError, match='broken'):
        with timing.measure('broken', 'a', 'tract_stage'):
            raise ValueError('broken')
    assert timing.rows[0]['status'] == 'failed'
    assert timing.rows[0]['elapsed_seconds'] >= 0


def test_failed_tract_records_stage_and_rollback(monkeypatch):
    script = Path(__file__).resolve().parents[1] / 'code/1-population-synthesis/run-synthesis-by-state.py'
    spec = importlib.util.spec_from_file_location('timed_synthesis', script)
    driver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(driver)

    class Sites:
        restored = False

        def snapshot(self):
            return 'snapshot'

        def restore(self, snapshot):
            assert snapshot == 'snapshot'
            self.restored = True

    def fail(*args):
        raise ValueError('broken fixture')

    monkeypatch.setattr(driver, '__create_individuals__', fail)
    school, daycare = Sites(), Sites()
    tract = type('Tract', (), {'name': '49035000100'})()
    timing = RunTiming()
    population, workplaces, verification, errors = [], [], [], []
    driver.__synthesize__(tract, None, None, None, school, daycare, None,
                          population, workplaces, verification, errors, timing=timing)
    assert school.restored and daycare.restored
    assert errors == [(tract.name, 'broken fixture')]
    assert population == workplaces == verification == []
    assert all(row['tract_status'] == 'failed' for row in timing.rows)
    stages = {row['stage']: row for row in timing.rows}
    assert stages['individual creation']['status'] == 'failed'
    assert stages['education rollback']['status'] == 'success'
    assert stages['tract total']['status'] == 'failed'
