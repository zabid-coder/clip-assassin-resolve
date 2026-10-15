"""Monitor and cancel only the render operation explicitly started by this job."""
import time
from config import config
from services.jobs import checkpoint


def render(project, job_ids):
    if project.IsRenderingInProgress(): raise ValueError('Wait for the existing Resolve render to finish.')
    available={job['JobId'] for job in project.GetRenderJobList() or []}
    if not job_ids or any(key not in available for key in job_ids):raise ValueError('A selected render job no longer exists. Queue the timelines again.')
    started=False
    try:
        checkpoint(5,'Starting the selected render jobs')
        if not project.StartRendering(job_ids):raise ValueError('Resolve could not start the selected render jobs')
        started=True;deadline=time.monotonic()+config.RENDER_TIMEOUT
        while time.monotonic()<deadline:
            states=[project.GetRenderJobStatus(key) or {} for key in job_ids]
            labels=[state.get('JobStatus',state.get('RenderStatus','')) for state in states]
            if any(label in ('Failed','Cancelled','Canceled') for label in labels):raise ValueError('A Resolve render failed or was cancelled. Check the Deliver queue.')
            if all(label=='Complete' for label in labels):
                started=False
                return {'success':True,'message':f'Rendered {len(job_ids)} videos successfully.'}
            progress=sum(float(state.get('CompletionPercentage',0)) for state in states)/len(states)
            checkpoint(progress,'Rendering selected videos in Resolve')
            time.sleep(.5)
        raise ValueError(f'Render exceeded the {config.RENDER_TIMEOUT}-second timeout')
    finally:
        if started:project.StopRendering()
