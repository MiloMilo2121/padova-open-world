"""Build (optional), launch, exercise and close the local Development survey Player.

Usage: python3 Tools/verify_survey.py --build
Evidence stays in .context. Runtime Pipeline never needs a Cloud connection.
"""
import argparse
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / '.context/build/PadovaCentro.app'
REPORT = ROOT / '.context/padova-player-verification.json'


def command(name, *args, runtime=True):
    cli = ['unity', 'command', name, *map(str, args), '--format', 'json']
    cli += ['--runtime-path', str(APP)] if runtime else ['--project-path', str(ROOT)]
    run = subprocess.run(cli, cwd=ROOT, capture_output=True, text=True, timeout=90)
    data = json.loads(run.stdout)
    if run.returncode or not data.get('success'):
        raise RuntimeError(f'{name}: {data.get("errors", run.stderr)}')
    result = data['data']['result']
    if isinstance(result, dict) and result.get('success') is False:
        raise RuntimeError(f'{name}: {result}')
    return result


def evaluate(code):
    result = command('eval', code)
    return result.get('result', result) if isinstance(result, dict) else result


def snapshot():
    # Pipeline's runtime compiler does not automatically reference custom asmdefs.
    # Read actual component fields through reflection, without changing game state.
    return evaluate('var e = UnityEngine.Camera.main.GetComponent("SurveyExplorer"); var t = e.GetType(); var s = t.GetField("Selected").GetValue(e); return new { position = new[] { e.transform.position.x, e.transform.position.y, e.transform.position.z }, plan = t.GetField("PlanView").GetValue(e), travelled = t.GetField("TravelledMetres").GetValue(e), selections = t.GetField("SelectionCount").GetValue(e), selected = s == null ? "" : s.GetType().GetField("SourceId").GetValue(s), views = t.GetField("ViewChanges").GetValue(e) };')


def key(name, seconds=0.12):
    command('simulate_key', '--key', name, '--action', 'down')
    try:
        time.sleep(seconds)
    finally:
        command('simulate_key', '--key', name, '--action', 'up')
    time.sleep(0.15)


def capture(filename):
    path = ROOT / '.context' / filename
    if path.exists():
        path.unlink()
    evaluate('UnityEngine.ScreenCapture.CaptureScreenshot(' + json.dumps(str(path)) + '); return "queued";')
    deadline = time.monotonic() + 10
    while not path.exists() and time.monotonic() < deadline:
        time.sleep(0.2)
    if not path.exists() or path.stat().st_size < 1000:
        raise RuntimeError('Screenshot not produced: ' + str(path))
    return str(path.relative_to(ROOT))


def main(build):
    if build:
        status = subprocess.run(['unity', 'status', '--format', 'json'], cwd=ROOT, capture_output=True, text=True, check=True)
        if not json.loads(status.stdout)['data']['count']:
            raise RuntimeError('Open the local Unity Editor first')
        command('build', '--target', 'StandaloneOSX', '--outputPath', str(APP), '--options', '["Development","AllowDebugging"]',
                '--scenes', '["Assets/Scenes/PadovaCentroSurvey.unity"]', '--confirm', 'true', runtime=False)
        deadline = time.monotonic() + 600
        while True:
            status = command('build_status', runtime=False)
            if status['status'] == 'completed':
                if status['result'] != 'Succeeded':
                    raise RuntimeError(str(status))
                break
            if time.monotonic() > deadline:
                raise TimeoutError('Build did not finish')
            time.sleep(2)
    log = open(ROOT / '.context/padova-player.log', 'w')
    player = subprocess.Popen([str(APP / 'Contents/MacOS/padova-open-world'), '-screen-fullscreen', '0', '-screen-width', '1600',
                               '-screen-height', '1000', '-logFile', str(ROOT / '.context/padova-player-unity.log')],
                              cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    report = {'scene': 'PadovaCentroSurvey', 'checks': [], 'screenshots': []}
    try:
        deadline = time.monotonic() + 60
        while True:
            try:
                status = command('runtime_status')
                break
            except Exception:
                if player.poll() is not None or time.monotonic() > deadline:
                    raise
                time.sleep(1)
        time.sleep(3)
        print('Player reachable; checking source scene and input.', flush=True)
        actual = evaluate('return UnityEngine.SceneManagement.SceneManager.GetActiveScene().name;')
        assert actual == 'PadovaCentroSurvey', actual
        before = snapshot()
        key('W', 0.6)
        moved = snapshot()
        distance = sum((a-b)**2 for a,b in zip(before['position'], moved['position'])) ** 0.5
        assert 15 < distance < 100, (before, moved)
        report['checks'].append({'name': 'W moves camera through Input System', 'metres': distance})
        key('R')
        reset = snapshot()
        assert sum(abs(a-b) for a,b in zip(before['position'], reset['position'])) < 0.1, reset
        report['checks'].append({'name': 'R restores overview', 'passed': True})
        report['screenshots'].append(capture('padova-survey-overview.png'))
        key('F')
        assert snapshot()['plan'] is True
        report['checks'].append({'name': 'F switches to plan view', 'passed': True})
        # Select a visible source volume at its actual projected centre using runtime pointer input.
        # A bounds centre may be inside a real courtyard. Use the importer's interior point.
        source = json.loads((ROOT / 'Data/PadovaCentro/derived/district.json').read_text())
        part = next(m for m in source['meshes'] if m['id'] == 'UN_VOL:35304:0')
        world = f"new UnityEngine.Vector3({part['x']:.6f}f, {part['eave']-15:.6f}f, {part['z']:.6f}f)"
        target = evaluate('var p = UnityEngine.Camera.main.WorldToScreenPoint(' + world + '); return new[] { p.x, p.y };')
        hit = evaluate(f'UnityEngine.RaycastHit hit; var ray = UnityEngine.Camera.main.ScreenPointToRay(new UnityEngine.Vector3({target[0]}f, {target[1]}f, 0)); return UnityEngine.Physics.Raycast(ray, out hit, 2000) ? hit.collider.name : "miss";')
        assert hit == 'UN_VOL:35304:0', hit
        command('simulate_pointer', '--x', target[0], '--y', target[1], '--action', 'down')
        time.sleep(0.2)
        command('simulate_pointer', '--x', target[0], '--y', target[1], '--action', 'up')
        selected = snapshot()
        assert selected['selected'] == 'UN_VOL:35304', selected
        report['checks'].append({'name': 'Pointer selects mapped building record', 'sourceId': selected['selected']})
        report['screenshots'].append(capture('padova-survey-plan.png'))
        key('Digit1')
        focused = snapshot()
        assert focused['plan'] is False
        assert abs(focused['position'][0] - 177.29894) < 0.1, focused
        report['checks'].append({'name': '1 focuses sourced Piazza delle Erbe anchor', 'passed': True})
        report['screenshots'].append(capture('padova-survey-erbe.png'))
        print('Input and feature selection verified; sampling short-run performance.', flush=True)
        report['performanceSamples'] = []
        for i in range(4):
            time.sleep(3)
            report['performanceSamples'].append(command('runtime_status'))
        report['passed'] = True
    except Exception as error:
        report['passed'] = False
        report['error'] = repr(error)
        raise
    finally:
        REPORT.write_text(json.dumps(report, indent=2) + '\n')
        try:
            command('quit')
        except Exception:
            player.terminate()
        try:
            player.wait(timeout=10)
        except subprocess.TimeoutExpired:
            player.kill()
            player.wait()
        log.close()
    print(json.dumps({k:v for k,v in report.items() if k != 'performanceSamples'}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', action='store_true')
    main(parser.parse_args().build)
