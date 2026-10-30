"""Manager SCA 唯讀收集抽象；無網路實作、憑證、排程或發佈副作用。"""
import copy
import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import quote


class CollectionError(ValueError):
    pass


def timestamp(value):
    t = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if t.tzinfo is None:
        raise CollectionError('時間缺少時區，須先依已驗證 API schema 正規化')
    return t.astimezone(timezone.utc)


class Collector:
    """transport.get(path, params) -> Wazuh data envelope。

    未來 transport 必須啟用 TLS 憑證與 hostname 驗證及逾時；此版只注入離線 fake。
    完整快照是回傳值；失敗以例外拒絕回傳，不發佈部分頁面。
    """
    def __init__(self, transport, page_size=100, max_pages=10000):
        if page_size < 1 or max_pages < 1:
            raise ValueError('分頁界限必須為正數')
        self.transport, self.page_size, self.max_pages = transport, page_size, max_pages

    def pages(self, path):
        items, raw, expected, offset = [], [], None, 0
        for _ in range(self.max_pages):
            try:
                response = copy.deepcopy(self.transport.get(path, {'offset': offset, 'limit': self.page_size}))
                data = response['data']
                batch, total = data['affected_items'], data['total_affected_items']
                if response.get('error', 0) or data.get('total_failed_items', 0) or data.get('failed_items'):
                    raise CollectionError('API 部分失敗')
                if not isinstance(total, int) or isinstance(total, bool) or total < 0 or not isinstance(batch, list):
                    raise CollectionError('分頁 schema 錯誤')
                if expected is None:
                    expected = total
                if total != expected or len(batch) > self.page_size or len(items)+len(batch) > total:
                    raise CollectionError('分頁總數不一致')
                raw.append(response)
                items.extend(batch)
                if len(items) == total:
                    return items, raw
                if not batch:
                    raise CollectionError('分頁提早結束')
                offset += len(batch)
            except CollectionError:
                raise
            except Exception as e:
                raise CollectionError('API/transport 讀取失敗') from e
        raise CollectionError('超出最大頁數')

    def collect(self, agent_id, policy_id, policy_hash, now=None, max_age_seconds=86400):
        if not agent_id or not policy_id or not policy_hash or max_age_seconds < 0:
            raise CollectionError('缺少識別、政策 hash 或時效設定錯誤')
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            raise CollectionError('擷取時間缺時區')
        path = '/sca/'+quote(str(agent_id), safe='')
        before, raw_before = self.pages(path)
        def select(rows):
            found = [r for r in rows if str(r.get('policy_id')) == policy_id]
            if len(found) != 1:
                raise CollectionError('政策不存在或重複')
            return found[0]
        summary = select(before)
        try:
            start, end = timestamp(summary['start_scan']), timestamp(summary['end_scan'])
            if start > end or end > now:
                raise CollectionError('掃描進行中或時間不合理')
            if summary['hash_file'] != policy_hash:
                raise CollectionError('政策 hash 不符')
            expected_count = summary['total_checks']
            if not isinstance(expected_count, int) or isinstance(expected_count, bool) or expected_count < 1:
                raise CollectionError('摘要控制項數量不合法')
        except (KeyError, TypeError, ValueError) as e:
            raise CollectionError('摘要缺少已驗證掃描時間/hash/數量') from e
        checks, raw_checks = self.pages(path+'/checks/'+quote(policy_id, safe=''))
        ids = [str(c.get('id')) for c in checks]
        if len(checks) != expected_count or len(set(ids)) != len(ids) or 'None' in ids:
            raise CollectionError('控制項缺漏或重複')
        after, raw_after = self.pages(path)
        if summary != select(after):
            raise CollectionError('掃描摘要變更；丟棄快照，呼叫端可有限次重試')
        canonical = json.dumps(dict(agent_id=agent_id, policy_id=policy_id, summary=summary,
            policy_hash=policy_hash, checks=sorted(checks, key=lambda c: str(c['id']))), sort_keys=True, separators=(',', ':'))
        return dict(snapshot_id=hashlib.sha256(canonical.encode()).hexdigest(), agent_id=agent_id,
                    policy_id=policy_id, policy_hash=policy_hash, summary=summary, checks=checks,
                    collected_at=now.isoformat(), stale=(now-end).total_seconds() > max_age_seconds,
                    complete=True, raw_pages=dict(before=raw_before, checks=raw_checks, after=raw_after))
