from services.ingest_plan import plan_ingest


def media(root, path):
    file=root/path
    file.parent.mkdir(parents=True,exist_ok=True)
    file.write_bytes(b'media')
    return file


def test_camera_day_card_orders_and_repeated_card_names(tmp_path):
    paths=['Raw Footages/Sony A7/Card 01/clip10.mov','Raw Footages/Sony A7/Card 01/clip2.mov',
           'Raw Footages/Day 01/FX3/Card 01/a.mp4','Raw Footages/Day 02/Card 01/a.mov',
           'Raw Footages/Smartphone/day 3/card 2/a.mov','Raw Footages/Canon/a.mov']
    for p in paths:media(tmp_path,p)
    result=plan_ingest(tmp_path)
    assert len(result['groups'])==5
    assert result['file_count']==6
    names=[g['timeline'] for g in result['groups']]
    assert len(set(names))==5
    assert 'Day 01 · FX3 · Card 01 Timeline' in names
    sony=next(g for g in result['groups'] if g['folder'].endswith('Sony A7/Card 01'))
    assert sony['files'][0].endswith('clip2.mov')


def test_card_storage_stays_together_and_parent_loose_files_separate(tmp_path):
    for p in ['Raw footage/Day 01/intro.mov','Raw footage/Day 01/Card 01/PRIVATE/M4ROOT/CLIP/c1.mp4',
              'Raw footage/Day 01/Card 01/PRIVATE/M4ROOT/CLIP/c2.mp4',
              'Raw footage/Day 01/Card 02/DCIM/100MEDIA/c3.mp4',
              'Raw footage/Day 01/Card 02/DCIM/101MEDIA/c4.mp4']:
        media(tmp_path,p)
    result=plan_ingest(tmp_path)
    assert [len(g['files']) for g in result['groups']]==[1,2,2]
    assert all('PRIVATE' not in g['timeline'] and 'DCIM' not in g['timeline'] for g in result['groups'])
    files=[p for g in result['groups'] for p in g['files']]
    assert len(files)==len(set(files))==5


def test_skips_generated_files_and_links_imports_audio_once(tmp_path):
    file=media(tmp_path,'Camera/Card 01/c.mov')
    media(tmp_path,'Exports/out.mov');media(tmp_path,'.hidden/secret.mov');media(tmp_path,'Audio/recording.wav')
    (tmp_path/'Camera'/'Card 01'/'alias.mov').symlink_to(file)
    (tmp_path/'Camera'/'duplicate.mov').hardlink_to(file)
    result=plan_ingest(tmp_path)
    assert result['file_count']==1
    assert result['audio_count']==1


def test_empty_root_and_multiple_raw_roots(tmp_path):
    assert plan_ingest(tmp_path)['groups']==[]
    media(tmp_path,'Raw/Day 01/Card 01/a.mov');media(tmp_path,'Footage/Day 01/Card 01/a.mov')
    result=plan_ingest(tmp_path)
    assert len({g['timeline'] for g in result['groups']})==2
    before=result['fingerprint']
    media(tmp_path,'Raw/Day 01/Card 01/b.mov')
    assert plan_ingest(tmp_path)['fingerprint']!=before


def test_case_and_delimiter_collisions_get_unique_names(tmp_path):
    media(tmp_path,'Footage/A · B/c.mov');media(tmp_path,'Footage/A - B/c.mov')
    assert len({g['timeline'] for g in plan_ingest(tmp_path)['groups']})==2
