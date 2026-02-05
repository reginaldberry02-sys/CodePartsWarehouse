sqlite3 "modules/registry/registry.sqlite" "PRAGMA table_info(scan_events);"

0|timestamp_utc|TEXT|1||0
1|scan_id|TEXT|1||0
2|artifact_type|TEXT|1||0
3|artifact_id|TEXT|1||0
4|parent_id|TEXT|0||0
5|supersedes_id|TEXT|0||0
6|superseded_by_id|TEXT|0||0
7|pyn_id|TEXT|0||0
8|sid_count|INTEGER|1|0|0
9|cid_count|INTEGER|1|0|0
10|capability|TEXT|0||0
11|standalone_status|TEXT|1|'none'|0
12|metadata_json|TEXT|0||0
13|use_env_first|TEXT|0||0
14|use_env_last|TEXT|0||0
15|use_env_seen_json|TEXT|0||0