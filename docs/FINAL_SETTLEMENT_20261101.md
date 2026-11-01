# LinuxGCB 最終結算報告（2026-11-01）

## 範圍與實作
- 基準：RHEL9 CIS GCB v1.2；母體 314 條，scope 307 條（Nftables 7 條依計畫排除）
- **實作 307/307**：base 270 ＋ sshd 32 ＋ firewalld 3
- 政策（Manager .53 `/var/ossec/etc/shared/linuxgcb/`，UNVALIDATED 旗標保留至人工複審完成）：
  - base sha256 `1d0be6df…`（FIX-10 版）｜sshd `a8840428…`（FIX-11 版）｜firewalld `fc861f55…`（FIX-8 版）

## 最終掃描 R26（agent010 / .61）
| 政策 | PASS | FAIL | 分數 |
|---|---|---|---|
| base | 128 | 142 | 47 |
| sshd | 32 | 0 | 100 |
| firewalld | 5 | 0 | 100 |
| **合計** | **165** | **142** | — |

## 142 FAIL 分類
| 類別 | 件數 | 性質 |
|---|---|---|
| 日誌與稽核 | 37 | 真實缺失（fixture R9/R12 已證明可全綠；永久套用與否待 Commander 決定） |
| 帳號與存取控制 | 35 | 真實缺失（pwquality/faillock/login.defs/TMOUT/umask/dconf 等全預設）；含 0229 accepted finding |
| 磁碟與檔案系統 | 33 | 真實缺失（19 條 modprobe 停用未設、/tmp 非 tmpfs 無選項、/home 無 nodev/nosuid/noexec 等） |
| 網路設定 | 22 | 真實缺失（sysctl 17＋協定模組 4＋無線 1；0123 需明確寫檔） |
| 系統設定與維護 | 14 | 真實缺失（AIDE、GRUB 通行碼、core dump、ASLR、0032 localpkg_gpgcheck、0038 EFI uid/gid 等） |
| SELinux | 1 | 0187 accepted finding |

## Accepted findings（Commander 2026-11-01 裁定：維持 FAIL、不矯正系統）
- 0187 未受限程序（Wazuh agent unconfined_service_t）
- 0229 sudo NOPASSWD（%wheel，自動化依賴）
詳見 docs/EXCEPTIONS.md。

## 已完成的真機加固（R13，備份於 /root/gcb-remediation-backup）
- SSH 12 條（0258/0263/0265/0266/0269/0272/0273/0275/0276/0277/0280/0315）→ sshd 32/32
- cron 8 條（crontab 600、cron 目錄 700、allow 檔、deny 檔移除）

## 規則品質修正鏈（FIX-1~11，全部真機實證零 side-effect）
- FIX-8：0244 systemd 單元不存在＝停用（R22 翻轉實證）
- FIX-9：0023-025 LV＝獨立 FS（轉 FAIL）、0073/074 $HOME 展開（轉 PASS）、0091 無 shadow＝PASS（R23 翻轉集合恰好 6 條）
- FIX-10：0032 純註解 repo 檔跳過＋合規範本 templates/gcb-gpgcheck.repo；真機雙向驗證 R24 PASS↔R25 FAIL（Commander 裁定程序）
- FIX-11：0282/0283 find 加偽 FS prune——R25 抓到 /proc churn flaky 假 FAIL，R26 穩定 PASS
- not-found 語意族（工具/單元/群組/section）已全數對齊來源條件式並獲 Commander 採認

## 驗證鏈
R7→R26 共 20 次引擎掃描；正向 fixture 雙向驗證兩輪（R9/R10、R12）＋ 0032 範本雙向（R24/R25）；每批部署前 argv_runner 真機預驗、部署後逐 check 翻轉集合比對。

## 待 Commander 決策（不影響結算）
1. 37 條日誌/稽核缺失是否永久套用 fixture 配方（注意 -e 2 鎖定與 logrotate 取代預設輪替）
2. 其餘真實缺失是否進行第二輪加固（帳號 35／磁碟 33／網路 22／系統 14）
3. ~~人工複審（UNVALIDATED→verified）與 exception 旗標是否進儀表板~~ → 已於 2026-11-01 完成（見下方補記）

## 補記（2026-11-01 当日收尾）
- FIX-12/12b/12c：Dashboard Description 轉合規值、人工檢核指令進 rationale、
  accepted finding 旗標（0187/0229）、報告 command 欄可讀化；R27/R28 零翻轉。
- FIX-13：Commander 回覆「均已驗證」→ 307 條治理狀態全轉 VERIFIED
  （live_validation=VALIDATED、execution_review=passed、source_approval=approved）；
  coverage partial 僅保留 108/141/269/270 範圍保留；政策 name/description 轉 VERIFIED。
- R29 引擎實證：三政策 hash 與部署值一致、名稱顯示 VERIFIED、307 條零翻轉（165P/142F）。
- 最終報表：reports/RHEL9_010_20261101_r29_snapshot.json、RHEL9_010_20261101_r29/
  （PASS 161＋MANUAL_PENDING 4＋FAIL 142）；驗收 docs/REALHOST_ACCEPTANCE_FIX13_R29.md。
- 專案狀態：**307/307 實作、真機驗收完成、人工複審 VERIFIED**。

## 報表產物
- reports/RHEL9_010_20261101_r26_snapshot.json、RHEL9_010_20261101_r26（HTML/CSV）
- 歷次驗收：docs/REALHOST_ACCEPTANCE_*.md、COMMANDER_RULINGS_20261101.md、EXCEPTIONS.md
