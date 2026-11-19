"""Create and verify a portable snapshot of the selected project sources."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import zipfile

root = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1]) if len(sys.argv) > 1 else root / 'backups'
out.mkdir(parents=True, exist_ok=True)
selected = [root/'server/promote_preview_service.py',root/'server/online.py',root/'tools/build_online_client.py',root/'tools/publish_online.py',root/'tools/verify_online.cjs',root/'test/test_online.py',root/'tools/publish_construction.py',root/'tools/verify_construction.cjs',root/'test/construction.test.mjs',root/'README.md', root/'AGENTS.md', Path(__file__)]
selected += [root/name for name in ('server/hub_auth.py','server/deploy_hub.py','server/deploy_gorod.py','tools/publish_gorod.py','tools/build_hub_client.py','tools/publish_hub.py','tools/account_fixture.py','tools/verify_accounts.cjs','tools/verify_hub_public.cjs','tools/verify_session.cjs','tools/verify_walk_start.cjs','tools/publish_walk_start.py','test/test_hub_auth.py','test/motion.test.mjs','tools/verify_motion.cjs','tools/publish_motion_preview.py','server/deploy_motion_preview.py','server/apply_gorod_update.py','tools/update_gorod.py')]
selected += sorted((root/'docs').glob('*.md'))
selected += [root/'art/ART-DIRECTION.md']
for folder in ('concepts','models','renders'):
    selected += sorted(p for p in (root/'art'/folder).iterdir()
                       if p.is_file() and ('town-v2' in p.name or 'panel-v3' in p.name or (folder=='concepts' and 'worker-v1' in p.name)))
selected += sorted(p for p in (root/'art/references').rglob('*') if p.is_file() and ('worker-motion-v4' not in p.parts or p.name in ('reference.mp4','reference.json','ANALYSIS.md')))
selected += [root/'art/production'/name for name in ('README.md','build_panel_v3.py','panel-config.json','render-panel-v3.sh','finalize_panel_v3.py','export_panel_sprites.py','PANEL-V3.md')]
selected += sorted(p for p in (root/'art/textures').rglob('*') if p.is_file() and 'ground-v1' not in p.parts)
selected += sorted(p for p in (root/'client').rglob('*') if p.is_file())
selected += sorted(p for p in (root/'.agent-skills').rglob('*') if p.is_file() and '__pycache__' not in p.parts)
selected += [root/'art/models/worker-v7.blend',root/'art/production/build_worker_v7.py',root/'art/production/finish_worker_v7_waist.py',root/'art/production/render_worker_v7_details.py',root/'tools/check_worker_v7_junctions.py',root/'tools/check_worker_model_v7.py',root/'tools/publish_worker_model_v7.py',root/'tools/verify_worker_model_v7.cjs']
selected += [root/'art/models/worker-v6.blend',root/'art/production/build_worker_v6.py',root/'art/production/fit_worker_v6_hat_only.py',root/'art/production/export_worker_model_v6.py',root/'art/production/refine_worker_v6_hat.py',root/'art/production/render_worker_v6_details.py',root/'tools/verify_worker_model_v6.cjs',root/'tools/check_worker_model_v6.py',root/'tools/publish_worker_model_v6.py']
selected += sorted(p for p in (root/'art/vendor/makehuman-v6').iterdir() if p.is_file())
selected += [root/'art/models/worker-v5.blend',root/'art/production/build_worker_v5.py',root/'art/production/export_worker_model_v5.py',root/'art/production/static_model_glb.py',root/'art/production/refine_worker_v5_face.py',root/'art/production/worker_mesh_v5.py',root/'tools/check_worker_model_v5.py',root/'tools/publish_worker_model_v5.py',root/'tools/verify_worker_model_v5.cjs']
selected += [root/'art/models'/name for name in ('worker-v3.blend','worker-v4.blend','birch-v1.blend')]
selected += [root/'art/production'/name for name in ('build_worker_v3.py','pack_worker_v3.py','worker_mesh_v3.py','gait_v3.py','build_birch.py','make_ground.py','prepare_ground_v2.py','gait_v4.py','retarget_worker_v4.py','export_worker_glb_lite.py','three-vendor-source.json')]
selected += [root/'tools'/name for name in ('preview_publish.py','publish_zoom.py','publish_gait.py','verify_scene.cjs','verify_gait.cjs','verify_zoom.cjs','verify_controls.cjs','check_gait.py','check_worker_rig.py','check_worker_actions.py','check_worker_v3.py','check_worker_v3_actions.py','check_gait_v3.py','verify_worker_v3.cjs','verify_worker_review.cjs','publish_worker_v3.py','render_worker_batch.sh','capture_scene.cjs','verify_surfaces.cjs','publish_surfaces.py','verify_motion_review.cjs','publish_motion_v4.py','check_motion_glb.py','check_gait_v4.py','capture_motion_v4.cjs')]
assert all(p.is_file() and not p.is_symlink() for p in selected)
files = {str(p.relative_to(root)): p.read_bytes() for p in selected}
manifest = {name: hashlib.sha256(data).hexdigest() for name,data in files.items()}
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
path = out / ('living-town-'+stamp+'.zip')
with zipfile.ZipFile(path, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for name,data in files.items(): z.writestr('living-town/'+name,data)
    z.writestr('living-town/art/textures/',b'')
    z.writestr('living-town/MANIFEST-SHA256.json',json.dumps(manifest,indent=2))
with zipfile.ZipFile(path) as z:
    assert z.testzip() is None
    for name,digest in manifest.items():
        assert hashlib.sha256(z.read('living-town/'+name)).hexdigest()==digest
sha = hashlib.sha256(path.read_bytes()).hexdigest()
path.with_suffix('.zip.sha256').write_text(sha+'  '+path.name+'\n')
print(json.dumps({'zip':str(path),'files':len(files),'source_bytes':sum(map(len,files.values())),
                  'zip_bytes':path.stat().st_size,'sha256':sha,'verified':True}))
