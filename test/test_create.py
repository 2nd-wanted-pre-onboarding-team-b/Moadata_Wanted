import pytest
from api import get_app
import json

# 이것만 사용한다.
CREATE_API = '/api/job/create'


@pytest.fixture
def api():
    app, api = get_app()
    yield app.test_client()


def check_only_status(api, req_job, answer_code):
    res = api.post(CREATE_API, data=json.dumps(req_job), content_type='application/json')
    assert res.status_code == answer_code


def test_no_over_two_graph(api):
    """
    그래프가 두개 이상이면 안된다.
    아래의 그래프는 R1으로 시작하는 그래프와
    R3로 시작한느 그래프가 따로 존재한다.
    """
    job = {
        'job_name': 'Job1',
        'job_list': {
            'R1': ['R2', 'W1'],
            'R2': ['W2'],
            'W1': ['W2'],
            'W2': [],
            'R3': ['W3'],
            'W3': [],
        },
        'property': {
            'R1': {'task_name': 'read', 'filename': 'init.csv'},
            'R2': {'task_name': 'read', 'fielname': 'a.csv'},
            'W1': {'task_name': 'write', 'filename': 'b.csv'},
            'W2': {'task_name': 'write', 'filename': 'c.csv'},
            'R3': {'task_name': 'read', 'filename': 'd.csv'},
            'W3': {'task_name': 'read', 'filename': 'e.csv'},
        }
    }
    check_only_status(api, job, 400)


def test_no_cycle_in_graph(api):
    """
    그래프가 순환을 돌아선 안된다.
    아래 그래프의 순환은 다음과 같다
    D -> W1 -> R2 -> D
    """
    job = {
        'job_name': 'Job1',
        'job_list': {
            'R1': ['D'],
            'R2': ['D'],
            'W1': ['R2'],
            'D': ['W1']
        },
        'property': {
            'R1': {'task_name': 'read', 'filename': 'init.csv'},
            'R2': {'task_name': 'read', 'fielname': 'a.csv'},
            'W1': {'task_name': 'write', 'filename': 'b.csv'},
            'D': {'task_name': 'drop', 'column_name': 'column1'},
        }
    }
    check_only_status(api, job, 400)


def test_no_double_of_one_edge(api):
    """
    동일한 간선이 두개 이상 중첩되면 안된다.
    """
    job = {
        'job_name': 'Job1',
        'job_list': {
            'R1': ['W1', 'W2'],
            'W1': ['D1'],
            'W2': ['D1'],
            'D1': [],
            'D2': ['W3', 'W4'],
            'W3': [],
            'W4': [],
        },
        'property': {
            'R1': {'task_name': 'read', 'filename': 'init.csv'},
            'W1': {'task_name': 'write', 'filename': 'a.csv'},
            'W2': {'task_name': 'write', 'filename': 'b.csv'},
            'W3': {'task_name': 'write', 'filename': 'c.csv'},
            'W4': {'task_name': 'write', 'filename': 'd.csv'},
            'D1': {'task_name': 'drop', 'column_name': 'column1'},
            'D2': {'task_name': 'drop', 'column_name': 'column2'},
        }
    }
    check_only_status(api, job, 400)


def test_property_size_not_match(api):
    """
    Job List의 Job과 Property의 Job 매칭이 안되는 경우
    """
    job = {
        'job_name': 'Job1',
        'job_list': {
            'R1': ['R2', 'W1'],
            'R2': ['W1', 'W2'],
            'W1': ['W2'],
            'W2': [],
        },
        'property': {
            'R1': {'task_name': 'read', 'filename': 'init.csv'},
            'R2': {'task_name': 'read', 'filename': '1.csv'},
            'W1': {'task_name': 'write', 'filename': 'a.csv'},
            'W3': {'task_name': 'write', 'filename': 'b.csv'},
        }
    }
    check_only_status(api, job, 400)


def test_property_read_failed(api):
    """
    Read Property 오류
    """
    job = {
        'job_name': 'Job1',
        'job_list': {
            'R1': ['R2', 'D1'],
            'R2': ['D1', 'W2'],
            'D1': ['W2'],
            'W2': [],
        },
        'property': {
            'R1': {'task_name': 'read', 'column_name': 'init.csv'},
            'R2': {'task_name': 'read', 'filename': '1.csv'},
            'D1': {'task_name': 'drop', 'column_name': 'col1'},
            'W2': {'task_name': 'write', 'filename': 'b.csv'},
        }
    }
    check_only_status(api, job, 400)


def test_property_write_failed(api):
    """
    write property 오류
    """
    job = {
        'job_name': 'Job1',
        'job_list': {
            'R1': ['R2', 'D1'],
            'R2': ['D1', 'W2'],
            'D1': ['W2'],
            'W2': [],
        },
        'property': {
            'R1': {'task_name': 'read', 'filename': 'init.csv'},
            'R2': {'task_name': 'read', 'filename': '1.csv'},
            'D1': {'task_name': 'drop', 'column_name': 'col1'},
            'W2': {'task_name': 'write', 'column_name': 'col1'},
        }
    }
    check_only_status(api, job, 400)


def test_property_drop_failed(api):
    """
    Drop Property 오류
    """
    job = {
        'job_name': 'Job1',
        'job_list': {
            'R1': ['R2', 'D1'],
            'R2': ['D1', 'W2'],
            'D1': ['W2'],
            'W2': [],
        },
        'property': {
            'R1': {'task_name': 'read', 'filename': 'init.csv'},
            'R2': {'task_name': 'read', 'filename': '1.csv'},
            'D1': {'task_name': 'drop', 'filename': 'init.csv'},
            'W2': {'task_name': 'write', 'filename': 'init.csv'},
        }
    }
    check_only_status(api, job, 400)


def test_success(api):
    """
    통과되어야 하는 케이스다
    """
    job = {
        'job_name': 'Job1',
        'job_list': {
            'R1': ['R2', 'W1'],
            'R2': ['W1', 'W2'],
            'W1': ['W2'],
            'W2': [],
        },
        'property': {
            'R1': {'task_name': 'read', 'filename': 'init.csv'},
            'R2': {'task_name': 'read', 'filename': '1.csv'},
            'W1': {'task_name': 'write', 'filename': 'a.csv'},
            'W2': {'task_name': 'write', 'filename': 'b.csv'},
        }
    }
    check_only_status(api, job, 400)
