from libs.resource_access import lock_while_using_file
from utils.jobdatabase.default_algorithm import search_job_by_job_id
from utils.jobdatabase.io import JobDatabaseRead, JobDatabaseWrite
from threading import Lock
from typing import Dict, Any, Optional
import json

from libs.validator import ValidatorChain
from utils.validator_chains import get_job_validator_chain


class JobDatabaseEngine:
    """
    Job.json을 관리하는 일종의 데이터베이스 엔진
    """

    """
    파일 접근은 한번에 하나의 클라이언트가 들어간다.
    파이썬에서는 동시에 접근할 경우 Error가 발생하기 때문에
    파일 접근을 시도할 때 먼저 Lock을 걸어둔다.
    """
    mutex: Lock

    """
    Job 데이터 상태가 유효한지를 파악하기 위한 Validator
    """
    validator: ValidatorChain

    def __new__(cls):
        """
        많은 트래픽으로 인한 Instance 남발을 줄이기 위해
        Singletone Pattern을 적용하여 하나의 인스턴스만 실행한다.
        """
        if not hasattr(cls, 'jobdatabase_instance'):
            cls.jobdatabase_instance = \
                super(JobDatabaseEngine, cls).__new__(cls)
        return cls.jobdatabase_instance

    def __init__(self):
        self.mutex = Lock()
        self.validator = get_job_validator_chain()

    def reset(self):
        """
        Job.json 초기화
        테스트 할 때만 사용
        """
        with JobDatabaseWrite() as w:
            json.dump({'jobs': []}, w, indent=4)

    def save(self, job: Dict[str, Any]) \
            -> (Optional[int], bool, Optional[Exception]):
        """
        새로운 Job을 json에 저장
        :returns (Job ID, success(True, False), Exception(if success then None)
        """
        @lock_while_using_file(self.mutex)
        def __save() -> int:
            """
            실제 파일에 저장
            Mutex Decorator를 적용하기 위해 파일 접근하는 함수를 따로 구현함
            """
            with JobDatabaseRead() as r:
                # json에 있는 Data Load
                storage = json.load(r)
                # job id 생성
                # 맨 마지막 job의 id에 1를 추가하는 방식
                new_job_id = 1 if len(storage['jobs']) == 0 else \
                    storage['jobs'][-1]['job_id'] + 1
            # job_id를 job에 추가 및 storage에 추가
            job['job_id'] = new_job_id
            storage['jobs'].append(job)
            # 파일에 작성
            with JobDatabaseWrite() as w:
                json.dump(storage, w, indent=4)
            # job_id 리턴
            return new_job_id

        # Validate 판정
        is_valid, err = self.validator(job)
        return                                          \
            (None, False, err) if not is_valid or err   \
            else (__save(), True, None)

    def update(self, job_id: int, updated_data: Dict[str, Any]):
        @lock_while_using_file(self.mutex)
        def __update():
            pass

        return __update()

    def get_item(self, job_id: int) \
            -> (Optional[Dict[str, Any]], bool, Optional[Exception]):
        """
        job_id에 대한 Job Data 얻기
        :param job_id:
        :return: (Result Data (None if not exists), is_success, the exception if get error)
        """
        @lock_while_using_file(self.mutex)
        def __get_item() -> (bool, Optional[Dict[str, Any]]):
            """
            파일에 직접 접근하여 데이터 구하기
            :return: ((True/False), Exception if has error while using file)
            """
            with JobDatabaseRead() as r:
                storage = json.load(r)['jobs']
                # idx -> job_id의 데이터가 위치해 있는 인덱스 값
                is_exists, idx = search_job_by_job_id(storage, job_id)
            if not is_exists:
                return False, None
            else:
                return True, storage[idx]
        try:
            # 파일에 접근해서 데이터 찾기
            success, res = __get_item()
        except Exception as e:
            # 파일 상의 에러 발생
            return None, False, e
        return                              \
            (res, True, None) if success    \
            else (None, False, ValueError(f"Failed to find id: {job_id}"))

    def remove(self, job_id: int):
        @lock_while_using_file(self.mutex)
        def __remove():
            pass

        return __remove()
