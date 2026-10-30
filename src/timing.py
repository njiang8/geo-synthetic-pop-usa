"""Measure synthesis runtime to identify stages worth optimizing."""
import csv
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter

from loguru import logger


class RunTiming:
    def __init__(self):
        self.rows = []

    @contextmanager
    def measure(self, stage, tract='', scope='run'):
        start = perf_counter()
        status = 'success'
        try:
            yield
        except BaseException:
            status = 'failed'
            raise
        finally:
            elapsed = perf_counter() - start
            self.rows.append(dict(scope=scope, tract=tract, stage=stage,
                                  elapsed_seconds=elapsed, status=status,
                                  tract_status=status if tract else ''))
            logger.info(f'Timing {tract or "run"}: {stage} {elapsed:.3f} s ({status})')

    def call(self, stage, function, *args, tract='', scope='run', **kwargs):
        with self.measure(stage, tract, scope):
            return function(*args, **kwargs)

    def finish_tract(self, first_row, tract, elapsed, status):
        for row in self.rows[first_row:]:
            row['tract_status'] = status
        self.rows.append(dict(scope='tract_total', tract=tract, stage='tract total',
                              elapsed_seconds=elapsed, status=status, tract_status=status))

    def summary(self):
        groups = {}
        for row in self.rows:
            # A completed stage in a failed tract belongs in the failed group too.
            outcome = row['tract_status'] or row['status']
            key = row['scope'], row['stage'], outcome
            groups.setdefault(key, []).append(row['elapsed_seconds'])
        return [dict(scope=scope, stage=stage, status=status, count=len(values),
                     total_seconds=sum(values), mean_seconds=sum(values) / len(values),
                     max_seconds=max(values))
                for (scope, stage, status), values in groups.items()]

    def report(self, path):
        summary = self.summary()
        with open(path, 'w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=[
                'scope', 'tract', 'stage', 'elapsed_seconds', 'status', 'tract_status'])
            writer.writeheader()
            writer.writerows(self.rows)
        summary_path = Path(path).with_name(Path(path).stem + '_summary.csv')
        with summary_path.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=[
                'scope', 'stage', 'status', 'count', 'total_seconds', 'mean_seconds', 'max_seconds'])
            writer.writeheader()
            writer.writerows(summary)
        logger.info('Timing summary (seconds; failed tracts grouped separately):\n'
                    'scope / stage / outcome | count | total | mean | max\n' + '\n'.join(
                        f"{r['scope']} / {r['stage']} / {r['status']} | {r['count']} | "
                        f"{r['total_seconds']:.3f} | {r['mean_seconds']:.3f} | {r['max_seconds']:.3f}"
                        for r in summary))
        logger.info(f'Timing records saved to {path}')
        logger.info(f'Timing averages and totals saved to {summary_path}')
