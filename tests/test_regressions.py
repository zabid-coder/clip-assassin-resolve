import os
import tempfile
from pathlib import Path
from unittest import mock


from fastapi.testclient import TestClient
from models.ingest_template import IngestTemplate, FolderNode, TemplateParameter
from services.template_engine import TemplateEngine
from services.builtin_templates import get_builtin_templates
from modules.ranges import normalize_ranges, invert_ranges
from time_parser import parse_time, parse_timecodes, frames_to_timecode
import server


def test_smpte_roundtrip():
    assert parse_time('00:01:00;00', 29.97) is None
    assert parse_time('00:01:00;02', 29.97) == 1800 / 29.97
    assert frames_to_timecode(1800, 29.97, True) == '00:01:00;02'
    for fps in (25, 30, 30000/1001, 60000/1001):
        for frames in (0, 100, 1800, 17982, 107892):
            drop = fps in (30000/1001, 60000/1001)
            assert round(parse_time(frames_to_timecode(frames, fps, drop), fps)*fps) == frames


def test_reject_bad_timestamps():
    assert parse_time('1:99') is None
    assert parse_time('00:00:00:30', 30) is None
    assert parse_time('1:2:3:4:5') is None
    assert parse_time('1.25') == 1.25
    assert parse_timecodes('1-2-3')[1]


def test_normalized_ranges():
    assert normalize_ranges([(-5,10),(5,20),(80,120)],100) == [(0,20),(80,100)]
    assert invert_ranges([(5,10),(8,15)],20) == [(0,5),(15,20)]


def test_builtin_preview_matches_disk(tmp_path):
    engine = TemplateEngine()
    for index, template in enumerate(get_builtin_templates()):
        target = tmp_path / str(index)
        values = {'project':'QA', 'client':'Client', 'date':'2026-10-15'}
        values.update({p.name: 'QA' for p in template.parameters if p.required and p.default is None})
        preview = engine.generate_structure(template, values, str(target), True)
        assert preview['success'], preview
        assert len(preview['preview']) > 10
        assert not target.exists()
        actual = engine.generate_structure(template, values, str(target))
        assert actual['success'], actual
        assert preview['preview'] == actual['created']
        assert all(Path(item['path']).exists() for item in actual['created'])


def test_loop_scope_and_preserve_existing(tmp_path):
    engine = TemplateEngine()
    template = IngestTemplate(id='test',name='Test',description='', parameters=[TemplateParameter(name='camera', label='Cameras', type='number',default='2')],
        structure=[FolderNode(name='Camera {camera}', loop_variable='camera',children=[FolderNode(name='{{camera}}.txt',type='file',placeholder_content='Camera {camera}')])])
    values={'project':'QA'}
    result=engine.generate_structure(template,values,str(tmp_path))
    assert result['success'], result
    path=tmp_path/'Camera 1'/'1.txt'
    assert path.read_text() == 'Camera 1'
    path.write_text('existing work')
    assert engine.generate_structure(template,values,str(tmp_path))['success']
    assert path.read_text() == 'existing work'


def test_path_escape_and_eval_blocked(tmp_path):
    engine=TemplateEngine()
    for name in ('../escape','/escape','..','bad\\name'):
        template=IngestTemplate(id='test',name='Test',description='',structure=[FolderNode(name=name)])
        assert not engine.generate_structure(template,{'project':'QA'},str(tmp_path))['success']
    template=IngestTemplate(id='test',name='Test',description='',structure=[FolderNode(name='safe',condition="().__class__.__base__.__subclasses__()")])
    assert not engine.generate_structure(template,{'project':'QA'},str(tmp_path))['success']
    assert not (tmp_path/'safe').exists()


def test_unique_api_routes():
    seen=set()
    for route in server.app.routes:
        for method in getattr(route,'methods',[]) or []:
            key=(method,route.path)
            assert key not in seen, key
            seen.add(key)


def test_template_crud_and_preview(tmp_path):
    with TestClient(server.app) as client:
        body={'name':'Saved QA','description':'Test','structure':[{'name':'{project}','children':[{'name':'Audio'}]}],'parameters':[]}
        created=client.post('/api/templates/create',json=body)
        assert created.status_code == 200, created.text
        template_id=created.json()['template']['id']
        assert client.get('/api/templates/'+template_id).json()['template']['name']=='Saved QA'
        assert any(t['id']==template_id for t in client.get('/api/templates').json()['templates'])
        preview=client.post('/api/templates/preview',json={'template_id':template_id,'parameters':{'project':'QA'},'base_path':str(tmp_path)})
        assert preview.json()['item_count']==2
        result=client.post('/api/templates/generate',json={'template_id':template_id,'parameters':{'project':'QA'},'base_path':str(tmp_path)})
        assert result.json()['total_items']==2
        assert (tmp_path/'QA'/'Audio').is_dir()
        assert client.delete('/api/templates/'+template_id).json()['success']
        assert client.get('/api/templates/'+template_id).status_code==404


def test_api_failures_have_json():
    with mock.patch.object(server.engine,'refresh',return_value=False), TestClient(server.app) as client:
        assert client.get('/api/nonexistent').status_code==404
        for endpoint,payload in [('cut',{'timecodes':'1-2'}),('pick_clips',{'names':'1'}),('merge_timelines',{'timeline_names':'x'}),('social_reframe',{'format':'9:16'}),('jl_cut',{}),('silence_remove',{})]:
            response=client.post('/api/'+endpoint,json=payload)
            assert response.status_code==200, response.text
            assert response.json()['success'] is False
        with mock.patch.object(server.engine, 'project', mock.Mock()):
            response=client.post('/api/silence_remove',json={'min_silence_ms':0})
            assert response.status_code==422


def test_asset_upload_and_traversal(tmp_path):
    with mock.patch.object(server.engine,'asset_directory',return_value=str(tmp_path)), TestClient(server.app) as client:
        assert client.post('/api/assets/upload?filename=../escape.png',content=b'x').status_code==400
        assert client.post('/api/assets/upload?filename=file.exe',content=b'x').status_code==400
        assert client.post('/api/assets/upload?filename=empty.png',content=b'').status_code==400
        assert client.post('/api/assets/upload?filename=test.png',content=b'png').status_code==200
        assert client.post('/api/assets/upload?filename=test.png',content=b'new').status_code==409
        assert (tmp_path/'test.png').read_bytes()==b'png'


def test_render_status_numeric_dimensions():
    from modules.audio_tools import get_render_status
    core=mock.Mock()
    core.project.GetRenderJobList.return_value=[{'JobId':'1','FormatWidth':1920,'FormatHeight':1080}]
    core.project.GetRenderJobStatus.return_value={'JobStatus':'Complete','CompletionPercentage':100}
    result=get_render_status(core)
    assert result['success']
    assert result['completed']==1
    assert result['jobs'][0]['format']=='1920x1080'


def test_failed_native_operation_is_not_success():
    from modules.export_tools import batch_render
    core=mock.Mock()
    core.project.GetRenderPresetList.return_value=[]
    core.project.GetTimelineCount.return_value=0
    result=batch_render(core,['missing'],'preset',tempfile.mkdtemp())
    assert result[0] is False


def test_waveform_sync_uses_current_api_options():
    from modules.magic_tools import auto_sync_audio
    core=mock.Mock()
    core.resolve.AUDIO_SYNC_WAVEFORM=0
    core.media_pool.GetSelectedClips.return_value=[mock.Mock(),mock.Mock()]
    core.media_pool.AutoSyncAudio.return_value=True
    assert auto_sync_audio(core)[0]
    options=core.media_pool.AutoSyncAudio.call_args.args[1]
    assert options['syncMode']==0
    assert 'audioSyncMode' not in options


def test_assembly_exact_partial_ranges_and_rollback():
    from modules.ranges import assemble_ranges
    core,source=mock.Mock(),mock.Mock()
    source.GetStartFrame.return_value=90000
    source.GetEndFrame.return_value=90100
    core.unique_timeline_name.return_value='Edited'
    item=mock.Mock();item.GetDuration.return_value=20
    core.media_pool.AppendToTimeline.return_value=[item]
    assert assemble_ranges(core,source,[(10,30)],'Edited')[0]
    info=core.media_pool.AppendToTimeline.call_args.args[0][0]
    assert info['startFrame']==10 and info['endFrame']==30
    item.GetDuration.return_value=19
    assert not assemble_ranges(core,source,[(10,30)],'Edited')[0]
    core.project.SetCurrentTimeline.assert_called_with(source)
    core.media_pool.DeleteTimelines.assert_called_once()


def test_invalid_custom_model_returns_422():
    with TestClient(server.app) as client:
        response=client.post('/api/templates/create',json={'name':'Bad','description':'','structure':[{'children':[]}],'parameters':[]})
        assert response.status_code==422


def test_master_folder_rejects_path_names(tmp_path):
    from modules.master_ingest import create_master_folder_structure
    for name in ('../escape','/escape','bad\\name'):
        assert not create_master_folder_structure(str(tmp_path),name)[0]
    assert not create_master_folder_structure(str(tmp_path),'Good',custom_date='bad-date')[0]
