#!/usr/bin/env python3
"""Inspect host tooling or simulate platform routing. Never execute device commands."""
from __future__ import annotations

import argparse
import json
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOLS = ('node', 'adb', 'hdc', 'java', 'appium', 'agent-device', 'xcrun', 'xcodebuild')
HOSTS = ('macos', 'windows', 'linux', 'unknown')
PHONES = ('ios', 'android', 'harmonyos_android', 'harmonyos', 'harmonyos_unknown', 'unknown')
SOURCES = {
    'agent-device': 'https://oss.callstack.com/agent-device/docs/installation',
    'android': 'https://github.com/appium/appium-uiautomator2-driver#requirements',
    'harmonyos': 'https://oss.callstack.com/agent-device/docs/commands#harmonyos-command-boundary',
    'ios-non-mac': 'https://appium.github.io/appium-xcuitest-driver/latest/guides/non-macos-hosts/',
}


def inspect_host(project: Path) -> dict:
    """PATH presence is not a successful version/driver/device readiness check."""
    host = {'Darwin': 'macos', 'Windows': 'windows', 'Linux': 'linux'}.get(platform.system(), 'unknown')
    paths = {name: shutil.which(name) for name in TOOLS}
    # npm project-local executables are often absent from PATH.
    for name in ('agent-device', 'appium'):
        for suffix in (('.cmd', '.exe', '') if host == 'windows' else ('',)):
            candidate = project / 'node_modules' / '.bin' / (name + suffix)
            if not paths[name] and candidate.is_file():
                paths[name] = str(candidate.resolve())
    version = None
    package = project / 'node_modules/agent-device/package.json'
    if package.is_file():
        try:
            version = json.loads(package.read_text(encoding='utf-8')).get('version')
        except (OSError, ValueError):
            pass
    return {'host': host, 'host_release': platform.release(), 'architecture': platform.machine(),
            'python': platform.python_version(), 'tools': paths, 'agent_device_package_version': version,
            'existing_ios_wrapper': all((project / p).exists() for p in ('scripts/iphone_device.py', 'agent_device_ios', 'config/app_cards')),
            'device_discovery': 'not_run'}


def plan(profile: dict, *, mode: str = 'capture', simulated: bool = False) -> dict:
    host, phone = profile.get('host', 'unknown'), profile.get('phone', 'unknown')
    if host not in HOSTS or phone not in PHONES:
        raise ValueError('未知的 host/phone 值')
    tools = profile.get('tools', {})
    if not isinstance(tools, dict):
        raise ValueError('tools 需要对象')
    for name in ('wda_available', 'remote_mac_available'):
        if type(profile.get(name, False)) is not bool:
            raise ValueError(f'{name} 必须为布尔值')
    ios_major = profile.get('ios_major')
    if ios_major is not None and (type(ios_major) is not int or ios_major < 1):
        raise ValueError('ios_major 需要正整数或 null')
    result = {'schema_version': 1, 'profile': profile, 'simulation': simulated,
              'detected_at': datetime.now(timezone.utc).isoformat(),
              'ready_for_capture': False, 'device_verified': False,
              'routing_status': 'needs_adaptation', 'backend': None, 'alternatives': [],
              'missing_tools': [], 'requirements': [], 'source_urls': [],
              'execution_policy': 'plan_only_no_install_no_device_commands',
              'next_steps': [], 'verification': '模拟/静态检查不能证明实机可用'}
    if mode == 'materials':
        result.update(backend='materials-only', routing_status='analysis_available',
                      next_steps=['直接登记材料与未知项，运行分析和报告校验；不进入设备适配。'])
        return result
    required = []
    if phone in ('unknown', 'harmonyos_unknown'):
        result.update(routing_status='needs_device_identity', next_steps=['先由用户说明手机系统，或在已授权采集任务内只读发现设备；不能由电脑系统推断手机。'])
        if phone == 'harmonyos_unknown':
            result['next_steps'] = ['确认华为手机型号和完整系统版本，区分Android兼容系统与原生鸿蒙；不能仅凭品牌或“鸿蒙”选择ADB/HDC，也不先安装两套工具。']
        return result
    if host == 'unknown':
        result.update(routing_status='needs_host_identity', next_steps=['确认实际运行终端及执行主机；不要将WSL或远程终端误当本机Windows。'])
        return result
    if phone in ('android', 'harmonyos_android'):
        result['backend'] = 'agent-device-android'
        result['alternatives'] = ['appium-uiautomator2: 优先路线出现已定位且无法修复的阻塞后再评估']
        required = ['node', 'adb', 'agent-device']
        result['source_urls'] = [SOURCES['android'], SOURCES['agent-device']]
        result['requirements'] = ['优先ADB + agent-device + Snapshot Helper，核对所装版本的Node/SDK/主机支持并锁定依赖', '手机USB调试及用户RSA授权；Helper安装提示由同学在手机上完成', '明确选择一台设备，处理offline/unauthorized', '适配目标App包名、实时元素结构和证据接口']
        if host == 'windows':
            result['requirements'].append('核对Windows架构、OEM USB驱动及原生终端；不能将WSL的Linux工具链与Windows adb.exe混用')
            result['requirements'].extend([
                '先读references/windows-adb-diagnostics.md：区分本地通信/服务失败、空列表、unauthorized、offline、多设备和device；接口枚举不等于ADB可用',
                '运行诊断由已授权的独立适配器步骤执行；优先复用兼容的健康ADB服务，不默认kill-server；满足条件时仅引导一次普通PowerShell初始化后回Codex复查',
                '每轮继续设备任务前复查权限作用域、服务和agent-device会话；Helper安装/解锁由用户完成，目标App截图不等于完整采集就绪',
            ])
    elif phone == 'harmonyos':
        result['backend'] = 'agent-device-harmonyos'
        required = ['node', 'hdc', 'agent-device']
        result['source_urls'] = [SOURCES['agent-device'], SOURCES['harmonyos']]
        result['requirements'] = ['优先HDC + 支持HarmonyOS的agent-device + ArkUI uitest；核对系统/API版本和当前设备capabilities，不套用Android APK Helper', '检查HDC命令行工具或DevEco SDK工具路径；不因PATH缺失就断定未安装', '由同学完成开发者模式、USB调试及设备授权，明确选择一台设备', '实现目标App安全封装和证据接口，在同学环境验证截图、页面结构、安全导航及返回']
        result['alternatives'] = ['优先路线经诊断仍缺必要能力时，依据官方HDC/uitest接口隔离补充适配器；不得退回Android Helper或盲目坐标回放']
    elif host == 'macos':
        result['backend'] = 'agent-device-ios'
        result['routing_status'] = 'existing_route_needs_preflight' if profile.get('existing_ios_wrapper') else 'needs_adaptation'
        required = ['node', 'agent-device', 'xcrun', 'xcodebuild']
        result['source_urls'] = [SOURCES['agent-device']]
        result['requirements'] = ['沿用当前版本和安全封装；不得因适配而自动升级', '检查Xcode、签名、设备信任与开发者模式', '运行原项目status及目标App冒烟；历史通过不代表当前就绪']
    else:
        result['source_urls'] = [SOURCES['ios-non-mac']]
        result['alternatives'] = ['已授权的远程Mac执行端', '同学已跑通的其他路线：先收集版本和操作证据', '用户截图/录屏材料分析']
        if ios_major is not None and ios_major >= 18 and profile.get('wda_available'):
            result['backend'] = 'appium-xcuitest-non-macos'
            required = ['node', 'appium']
            result['requirements'] = ['仅真机：复核iOS>=18及驱动兼容版本', '核对预装或外部WDA的签名、运行及可达性，不在Windows上调用xcodebuild', '核对appium-ios-remotexpc与本机前置条件，建立受授权的RemoteXPC通道', '显式登记udid、platformVersion及WDA启动方式，不能自动选设备']
        elif profile.get('remote_mac_available'):
            result['backend'] = 'remote-mac-ios'
            result['requirements'] = ['只使用用户已授权且可达的执行端；远端连接目标iPhone', '验证身份、签名、会话归属、证据回传与断线退出', '远端也须通过目标App实测；本地已装工具不证明远端就绪']
        else:
            result['routing_status'] = 'needs_ios_prerequisites'
            result['backend'] = 'research-ios-route'
            result['requirements'] = ['确认iOS版本以及预装/外部WDA条件', '不满足本机候选条件时评估已授权的远端或同学成功方案', '缺条件时保留材料分析，不能宣称所有Windows+iPhone方案不可行']
    result['missing_tools'] = [name for name in required if not tools.get(name)]
    result['next_steps'] = [
        '先向同学说明检测结果、推荐路线、AI将完成的配置及需要手动确认的步骤；只追问影响分流的缺失信息。',
        '检测/适配失败先由AI读取现有证据、查对应方案并执行已授权修复；优先用可用终端/API或同学电脑上的电脑控制工具代操作，必要人工动作每次只给一步及成功标志，由AI复查后继续。',
        '同学反馈成功记为user_reported；拿不到原技术路径或教师电脑无法验收，不阻塞在同学环境重建与验证。',
        '读取所选路线官方文档与本机版本，写adaptation-plan.json；只研究当前缺口，不自动遍历安装所有框架。',
        '若当前任务授权建设环境，隔离实现适配器并做本地测试；需要用户完成设备信任或系统权限时仅停在该步。',
        '失败时保存报错，按连接/工具版本/页面能力/封装接口定位，实施最小修复后复测；同一阻塞无新证据不反复重试。',
        '完成目标App打开、读取结构、截图、安全导航和返回的留证测试，并验证交易拦截，再允许正式采集。',
    ]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('inspect', 'simulate'))
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--host', choices=HOSTS)
    parser.add_argument('--phone', choices=PHONES, default='unknown')
    parser.add_argument('--mode', choices=('materials', 'capture'), default='capture')
    parser.add_argument('--tools', nargs='*', choices=TOOLS, default=None)
    parser.add_argument('--ios-major', type=int)
    parser.add_argument('--wda-available', action='store_true')
    parser.add_argument('--remote-mac-available', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.command == 'inspect':
        if args.host or args.tools is not None:
            parser.error('inspect 不允许伪造 host/tools；请用 simulate')
        profile = inspect_host(args.project.resolve())
    else:
        if not args.host:
            parser.error('simulate 需要 --host')
        profile = {'host': args.host, 'tools': {x: True for x in (args.tools or [])}, 'device_discovery': 'not_run'}
    profile.update(phone=args.phone, phone_source='unknown' if args.phone == 'unknown' else 'simulated' if args.command == 'simulate' else 'user_declared',
                   ios_major=args.ios_major, wda_available=args.wda_available, remote_mac_available=args.remote_mac_available)
    result = plan(profile, mode=args.mode, simulated=args.command == 'simulate')
    text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding='utf-8')
    print(text, end='')
    return 0  # A plan was produced. Consult ready_for_capture; zero is not readiness.


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        raise SystemExit(1)
