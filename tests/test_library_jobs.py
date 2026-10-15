import hashlib
import json
from pathlib import Path
import threading
import time
import zipfile
from unittest import mock
import pytest
from fastapi.testclient import TestClient
import server
from services import library,workflows,integrations
from services.jobs import JobManager,JobCancelled


@pytest.fixture
def package(tmp_path,monkeypatch):
    bundled=tmp_path/'bundled';folder=bundled/'sample';folder.mkdir(parents=True)
    archive=folder/'Sample.drfx'
    with zipfile.ZipFile(archive,'w') as z:
        z.writestr('Edit/Titles/Test/Sample.setting','{ Tools = ordered() { } }')
        z.writestr('Edit/Titles/Test/Sample.png',b'png')
        z.writestr('__MACOSX/Edit/Titles/Test/._Sample.setting',b'ignored')
    data={'id':'sample','name':'Sample','file':'sample/Sample.drfx','sha256':library.sha(archive),
          'bytes':archive.stat().st_size,'bundled':True,'categories':['Titles'],'template_count':1,
          'locations':['Effects Library → Titles → Test'],'fonts':[],'notes':[],'dependencies':[],'preview':None}
    (bundled/'catalog.json').write_text(json.dumps({'packages':[data]}))
    monkeypatch.setattr(library,'BUNDLED',bundled)
    monkeypatch.setattr(library.db,'data_dir',str(tmp_path/'state'))
    monkeypatch.setenv('CLIP_ASSASSIN_FUSION_DIR',str(tmp_path/'Fusion'))
    return data,tmp_path/'Fusion'


def test_all_bundled_packages_self_contained():
    items=library.packages()
    bundled=[p for p in items if p.get('bundled')]
    assert len(bundled)==12
    assert sum(p['template_count'] for p in bundled)==547
    assert max(p['bytes'] for p in bundled)>150*1024**2
    for package in bundled:
        path=library.package_path(package)
        assert library.sha(path)==package['sha256']
        assert library.archive_entries(path)
        for dependency in package['dependencies']:
            assert library.sha(path.parent/dependency['path'])==dependency['sha256']
        for note in package['notes']:assert (path.parent/note['path']).is_file()


def test_install_verify_repair_remove(package):
    data,root=package
    assert library.install('sample')['success']
    assert library.install_status(data,True)['state']=='installed'
    target=root/'Templates/Edit/Titles/Test/Sample.setting'
    target.write_text('external change')
    assert library.install_status(data,True)['state']=='needs_repair'
    with pytest.raises(ValueError):library.uninstall('sample')
    assert library.install('sample',True)['success']
    assert library.uninstall('sample')['success']
    assert not target.exists()


def test_backup_and_restore_original(package):
    _,root=package
    target=root/'Templates/Edit/Titles/Test/Sample.setting';target.parent.mkdir(parents=True);target.write_text('original work')
    with pytest.raises(ValueError):library.install('sample')
    assert target.read_text()=='original work'
    assert library.install('sample',True)['success']
    assert library.uninstall('sample')['success']
    assert target.read_text()=='original work'


def test_install_cancellation_rolls_back(package,monkeypatch):
    _,root=package
    def cancel(progress=None,message=None):
        if progress is not None and progress>45:raise JobCancelled('test cancellation')
    monkeypatch.setattr(library,'checkpoint',cancel)
    with pytest.raises(JobCancelled):library.install('sample')
    assert not (root/'Templates/Edit/Titles/Test/Sample.setting').exists()
    assert not library.manifest_path('sample').exists()


def test_archive_traversal_rejected(tmp_path):
    archive=tmp_path/'bad.drfx'
    with zipfile.ZipFile(archive,'w') as z:z.writestr('../outside.setting','bad')
    with pytest.raises(ValueError):library.archive_entries(archive)


def test_folder_scan_deduplicates(package):
    data,_=package
    result=library.scan_folder(str(library.package_path(data).parent))
    assert result['added']==[]


def test_font_unknown_is_not_claimed_missing(monkeypatch):
    monkeypatch.setattr(library,'font_families',lambda:None)
    assert library.font_status({'family':'Not Sure','url':''})['status']=='needs_checking'


def wait_for_job(manager,key):
    deadline=time.monotonic()+3
    while time.monotonic()<deadline:
        job=manager.get(key)
        if job['status'] not in ('queued','running','cancelling'):return job
        time.sleep(.01)
    raise AssertionError('Job did not finish')


def test_job_history_and_cancel(tmp_path):
    manager=JobManager(tmp_path/'jobs.db')
    entered=threading.Event()
    def run(operation,payload,context,source):
        entered.set()
        for i in range(50):context.update(i,'working');time.sleep(.01)
        return {'success':True,'message':'done'}
    job=manager.submit('test',{},run)
    assert entered.wait(1)
    manager.cancel(job['id'])
    result=wait_for_job(manager,job['id'])
    assert result['status']=='cancelled'
    manager.pool.shutdown()
    restored=JobManager(tmp_path/'jobs.db')
    assert restored.get(job['id'])['status']=='cancelled'
    restored.pool.shutdown()


def test_restart_marks_unfinished_job(tmp_path):
    database=tmp_path/'jobs.db';manager=JobManager(database)
    manager.persist({'id':'unfinished','status':'running','created_at':'2026-10-15T00:00:00+00:00'})
    manager.pool.shutdown()
    restored=JobManager(database)
    assert restored.get('unfinished')['status']=='interrupted'
    restored.pool.shutdown()


def test_signed_preview_and_tamper(package):
    review=workflows.preview(mock.Mock(),'library_install',{'package_id':'sample'})
    assert review['ready']
    body=workflows.read_token(review['preview_token'])
    assert body['operation']=='library_install'
    with pytest.raises(ValueError):workflows.read_token(review['preview_token']+'0')


def test_pinned_project_prevents_wrong_timeline():
    core=mock.Mock();core.project.GetName.return_value='Changed'
    core.project.GetCurrentTimeline.return_value=None
    context=mock.Mock()
    with pytest.raises(ValueError,match='changed after preview'):
        workflows.runner(core)('snapshot',{},context,{'project':'Original','timeline_id':'123'})
    core.create_snapshot.assert_not_called()


def test_cloud_requires_explicit_media_consent(tmp_path):
    media=tmp_path/'test.wav';media.write_bytes(b'wav')
    with pytest.raises(ValueError,match='Confirm'):
        integrations.transcribe({'provider':'openai','audio_path':str(media),'allow_cloud':False})
    with pytest.raises(ValueError,match='Confirm'):
        integrations.youtube_upload({'allow_cloud':False})


def test_capture_only_directory_names(tmp_path):
    from services.folder_presets import capture
    (tmp_path/'Raw/Card 01').mkdir(parents=True);(tmp_path/'Raw/Card 01/footage.mov').write_bytes(b'private media')
    data=capture(str(tmp_path))
    assert data['folder_count']==3
    assert 'footage.mov' not in json.dumps(data)


def test_folder_job_api_end_to_end(tmp_path):
    with TestClient(server.app) as client:
        template=client.post('/api/templates/create',json={'name':'Job preset','description':'','structure':[{'name':'{project}','children':[{'name':'Raw'}]}],'parameters':[]}).json()['template']
        payload={'operation':'folder_generate','payload':{'template_id':template['id'],'parameters':{'project':'Test'},'base_path':str(tmp_path)}}
        review=client.post('/api/jobs/preview',json=payload)
        assert review.status_code==200 and review.json()['ready']
        submitted=client.post('/api/jobs',json={'preview_token':review.json()['preview_token']})
        assert submitted.status_code==200,submitted.text
        job=wait_for_job(server.jobs,submitted.json()['job']['id'])
        assert job['status']=='succeeded',job
        assert (tmp_path/'Test/Raw').is_dir()
        assert job['result']['target']==str(tmp_path/'Test')
        assert client.post('/api/jobs/'+job['id']+'/retry',json={}).status_code==400


def test_job_models_strip_unknown_secrets():
    data=workflows.validate('snapshot',{'api_key':'should never be saved'})
    assert data=={}


def test_renderer_cancels_only_its_own_start(monkeypatch):
    from services import render_jobs
    project=mock.Mock()
    project.IsRenderingInProgress.return_value=False
    project.GetRenderJobList.return_value=[{'JobId':'owned'}]
    project.StartRendering.return_value=True
    project.GetRenderJobStatus.return_value={'JobStatus':'Rendering','CompletionPercentage':25}
    calls=[]
    def cancel(progress=None,message=None):
        calls.append(progress)
        if len(calls)>1:raise JobCancelled('cancel')
    monkeypatch.setattr(render_jobs,'checkpoint',cancel)
    with pytest.raises(JobCancelled):render_jobs.render(project,['owned'])
    project.StopRendering.assert_called_once()
    project.IsRenderingInProgress.return_value=True
    project.StopRendering.reset_mock()
    with pytest.raises(ValueError,match='existing'):render_jobs.render(project,['owned'])
    project.StopRendering.assert_not_called()


def test_renderer_completes(monkeypatch):
    from services.render_jobs import render
    project=mock.Mock();project.IsRenderingInProgress.return_value=False
    project.GetRenderJobList.return_value=[{'JobId':'owned'}]
    project.StartRendering.return_value=True
    project.GetRenderJobStatus.return_value={'JobStatus':'Complete','CompletionPercentage':100}
    assert render(project,['owned'])['success']
    project.StopRendering.assert_not_called()


def test_macos_metadata_is_not_installed(tmp_path):
    archive=tmp_path/'metadata.drfx'
    with zipfile.ZipFile(archive,'w') as z:
        z.writestr('Edit/.DS_Store','finder metadata')
        z.writestr('Edit/Titles/.DS_Store','finder metadata')
        z.writestr('Edit/Titles/Actual.setting','template')
    assert len(library.archive_entries(archive))==1


def test_shared_package_file_removed_only_after_last_owner(package):
    data,root=package
    duplicate={**data,'id':'second-package'}
    manifest=library.BUNDLED/'catalog.json'
    manifest.write_text(json.dumps({'packages':[data,duplicate]}))
    library.install('sample')
    library.install('second-package')
    target=root/'Templates/Edit/Titles/Test/Sample.setting'
    library.uninstall('sample')
    assert target.exists()
    library.uninstall('second-package')
    assert not target.exists()
