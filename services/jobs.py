"""Single-worker local jobs with durable history and cooperative cancellation."""
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
import time
from uuid import uuid4
import db

native_lock = threading.Lock()
_current = ContextVar('clip_assassin_job', default=None)


class JobCancelled(Exception):
    pass


class JobContext:
    def __init__(self, manager, job_id):
        self.manager, self.id = manager, job_id

    def check(self):
        if self.manager.events[self.id].is_set():
            raise JobCancelled('Cancelled at a safe checkpoint. Some completed steps may remain. Inspect the output before retrying.')

    def update(self, progress=None, message=None):
        self.check()
        with self.manager.lock:
            job = self.manager.jobs[self.id]
            if progress is not None: job['progress'] = max(job['progress'], min(99, round(progress)))
            if message:
                job['message'] = message
                job['logs'] = (job['logs'] + [{'time': datetime.now(timezone.utc).isoformat(), 'message': message}])[-100:]
            self.manager.persist(job)


def checkpoint(progress=None, message=None):
    context = _current.get()
    if context: context.update(progress, message)


class JobManager:
    def __init__(self, database=None):
        self.database = str(database or db.DB_PATH)
        self.lock = threading.RLock()
        self.jobs, self.events = {}, {}
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='clip-assassin-job')
        import sqlite3
        with sqlite3.connect(self.database) as connection:
            connection.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, data TEXT NOT NULL)')
            for key, data in connection.execute('SELECT id,data FROM jobs'):
                job = json.loads(data)
                if job['status'] in ('queued','running','cancelling'):
                    job.update(status='interrupted', finished_at=datetime.now(timezone.utc).isoformat(), message='The app closed before this job finished. Inspect the result before retrying.')
                    connection.execute('UPDATE jobs SET data=? WHERE id=?',(json.dumps(job), key))
                self.jobs[key] = job
                self.events[key] = threading.Event()

    def persist(self, job):
        import sqlite3
        with sqlite3.connect(self.database) as connection:
            connection.execute('INSERT OR REPLACE INTO jobs VALUES (?,?)', (job['id'],json.dumps(job,ensure_ascii=False)))

    def submit(self, operation, payload, runner, source=None, retry_of=None):
        job_id = uuid4().hex
        with self.lock:
            if sum(j['status'] in ('queued','running','cancelling') for j in self.jobs.values()) >= 20:
                raise ValueError('The queue is full. Wait for a job to finish.')
            job = {'id':job_id,'operation':operation,'payload':payload,'source':source or {},'retry_of':retry_of,
                'status':'queued','progress':0,'message':'Waiting to start','logs':[],
                'created_at':datetime.now(timezone.utc).isoformat(),'started_at':None,'finished_at':None,'result':None}
            self.jobs[job_id] = job; self.events[job_id] = threading.Event(); self.persist(job)
        self.pool.submit(self._run, job_id, runner)
        return self.get(job_id)

    def _run(self, job_id, runner):
        job = self.jobs[job_id]; context = JobContext(self, job_id)
        token = _current.set(context)
        try:
            context.check()
            with self.lock:
                job.update(status='running',started_at=datetime.now(timezone.utc).isoformat()); self.persist(job)
            result = runner(job['operation'], job['payload'], context, job['source'])
            if isinstance(result, tuple): result = {'success':bool(result[0]),'message':str(result[1])}
            if not isinstance(result, dict): result = {'success':True,'message':str(result)}
            # A finished non-interruptible native call is recorded as finished, even if Cancel was requested.
            status = 'succeeded' if result.get('success') else 'failed'
            with self.lock: job.update(status=status,result=result,message=result.get('message','Completed'),progress=100 if status=='succeeded' else job['progress'])
        except JobCancelled as exc:
            with self.lock: job.update(status='cancelled',message=str(exc),result={'success':False,'message':str(exc)})
        except Exception as exc:
            import logging
            logging.getLogger(__name__).exception('Job failed: %s',job['operation'])
            with self.lock: job.update(status='failed',message=str(exc),result={'success':False,'message':str(exc)})
        finally:
            with self.lock:
                job['finished_at'] = datetime.now(timezone.utc).isoformat(); self.persist(job)
            _current.reset(token)

    def get(self, job_id):
        with self.lock:
            job = self.jobs.get(job_id)
            if not job: return None
            result = json.loads(json.dumps(job))
            # Credentials are never persisted in payloads or exposed in job results.
            start = job.get('started_at') or job['created_at']
            end = job.get('finished_at') or datetime.now(timezone.utc).isoformat()
            result['elapsed_seconds'] = round((datetime.fromisoformat(end)-datetime.fromisoformat(start)).total_seconds(),1)
            return result

    def list(self):
        with self.lock: ids = sorted(self.jobs,key=lambda i:self.jobs[i]['created_at'],reverse=True)[:100]
        return [self.get(i) for i in ids]

    def cancel(self, job_id):
        with self.lock:
            job = self.jobs.get(job_id)
            if not job: raise ValueError('Job not found')
            if job['status'] in ('queued','running','cancelling'):
                self.events[job_id].set()
                job['status'] = 'cancelling'
                job['message'] = 'Cancellation requested. Waiting for the next safe checkpoint; an in-flight Resolve call must finish.'
                self.persist(job)
        return self.get(job_id)
