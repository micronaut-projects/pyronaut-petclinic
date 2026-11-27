"""Direct interval query contracts from Java VisitRepositoryTest."""

import pytest
from petclinic_test_support import DATABASE

pytestmark = pytest.mark.skipif(DATABASE != 'oracle', reason='Oracle-only reference feature')



@pytest.fixture
def visit_repository(application_context):
    import java
    return application_context.java_ctx.getBean(java.type('petclinic.repositories.VisitRepository'))


def test_visit_interval_repository_reads_values(visit_repository):
    from petclinic.services.durations import duration_minutes
    visits = visit_repository.findByPetName('Samantha')
    assert [duration_minutes(v.duration) for v in visits] == [60, 30]
    assert [v.period.toTotalMonths() for v in visits] == [12, 6]


@pytest.mark.parametrize('method,bound,inclusive,greater', [
    ('findByDurationGreaterThan', 180, False, True),
    ('findByDurationGreaterThanEqual', 210, True, True),
    ('findByDurationLessThanEqual', 45, True, False),
    ('findByPeriodGreaterThan', 24, False, True),
    ('findByPeriodGreaterThanEqual', 24, True, True),
    ('findByPeriodLessThanEqual', 6, True, False),
])
def test_visit_interval_repository_bounds(visit_repository, method, bound, inclusive, greater):
    from java.time import Duration, Period
    from petclinic.services.durations import duration_minutes
    duration = 'Duration' in method
    limit = Duration.ofMinutes(bound) if duration else Period.ofMonths(bound).normalized()
    visits = getattr(visit_repository, method)(limit)
    values = [duration_minutes(v.duration) if duration else v.period.toTotalMonths() for v in visits]
    assert values
    if inclusive:
        assert bound in values
        assert all(v >= bound if greater else v <= bound for v in values)
    else:
        assert all(v > bound if greater else v < bound for v in values)


def test_visit_interval_repository_combined_bounds(visit_repository):
    from java.time import Duration, LocalDate, Period
    from petclinic.services.durations import duration_minutes
    visits = visit_repository.findByDateBetweenAndDurationLessThanEqualsAndPeriodLessThanEquals(
        LocalDate.parse('2017-01-01'), LocalDate.parse('2020-12-31'),
        Duration.ofMinutes(90), Period.ofMonths(18).normalized())
    assert len(visits) == 4
    assert all('2017-01-01' <= str(v.date) <= '2020-12-31' and
               duration_minutes(v.duration) <= 90 and v.period.toTotalMonths() <= 18 for v in visits)


def test_visit_interval_repository_text_pet_and_date_queries(visit_repository):
    from java.time import LocalDate
    assert visit_repository.findByPetIdIn([7, 8])
    assert visit_repository.findByDescriptionContainingIgnoreCase('RaBiEs')
    after = visit_repository.findByDateGreaterThanEqual(LocalDate.parse('2026-01-05'))
    before = visit_repository.findByDateLessThanEqual(LocalDate.parse('2019-01-01'))
    assert after and all(str(v.date) >= '2026-01-05' for v in after)
    assert before and all(str(v.date) <= '2019-01-01' for v in before)
