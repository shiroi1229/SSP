#!/usr/bin/env python
"""
Auto-invokes roadmap sync when UI files change in a commit.
"""
import subprocess
import sys
from pathlib import Path

VERSION_CONFIG = {
    'UI-v3.0': {
        'progress': 75,
        'features': ['frontend/components/dashboard/MetaContractConsole.tsx'],
        'details': 'Meta-Contract Console updated with trace panel and Awareness alignment.',
        'globs': ['frontend/components/dashboard/MetaContractConsole.tsx'],
    },
    'UI-v3.3': {
        'progress': 55,
        'features': ['frontend/components/dashboard/SharedMindConsole.tsx', 'frontend/components/dashboard/SharedRealityNetworkPanel.tsx'],
        'details': 'Shared Mind Console gained the Shared Reality Network visualization.',
        'globs': ['frontend/components/dashboard/SharedMindConsole.tsx', 'frontend/components/dashboard/SharedRealityNetworkPanel.tsx'],
    },
    'UI-v3.5': {
        'progress': 40,
        'features': ['frontend/components/dashboard/MetaAwarenessFeed.tsx', 'frontend/components/dashboard/MetaAwarenessTimeline.tsx'],
        'details': 'Meta-Awareness timeline and Shared Reality link updated.',
        'globs': ['frontend/components/dashboard/MetaAwarenessFeed.tsx', 'frontend/components/dashboard/MetaAwarenessTimeline.tsx'],
    },
}

def get_changed_files():
    prev = subprocess.run(['git', 'rev-parse', 'HEAD^'], capture_output=True, text=True)
    if prev.returncode != 0:
        return []
    diff = subprocess.run(['git', 'diff', '--name-only', 'HEAD^', 'HEAD'], capture_output=True, text=True)
    if diff.returncode != 0:
        return []
    return [line.strip() for line in diff.stdout.splitlines() if line.strip()]

def matches_glob(path, glob_patterns):
    from pathlib import Path
    p = Path(path)
    for pattern in glob_patterns:
        if p.match(pattern):
            return True
    return False

def run_sync(version, config):
    cmd = [
        sys.executable, 'scripts/sync_roadmap_ui.py',
        '--version', version,
        '--progress', str(config['progress']),
        '--details', config['details'],
    ]
    cmd.extend(['--features', *config['features']])
    subprocess.run(cmd)

def main():
    changed = get_changed_files()
    if not changed:
        return
    for version, config in VERSION_CONFIG.items():
        globs = config['globs']
        if any(matches_glob(path, globs) for path in changed):
            run_sync(version, config)

if __name__ == '__main__':
    main()
