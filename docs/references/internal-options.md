Source: https://documentation.wazuh.com/current/user-manual/reference/internal-options.html

Contact us

# Internal configuration [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/reference/internal-options.html\#internal-configuration "Permalink to this headline")

The main configuration is located in the `ossec.conf` file, however some internal configuration features are located in the `/var/ossec/etc/internal_options.conf` file.

Generally, this file is reserved for debugging issues and for troubleshooting. **Any error in this file may cause your installation to malfunction or fail to run.**

Note

This file will be overwritten during upgrades. In order to maintain custom changes, you must use the `/var/ossec/etc/local_internal_options.conf` file.

## Agent [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/reference/internal-options.html\#agent "Permalink to this headline")

|     |     |     |
| --- | --- | --- |
| **agent.tolerance** | Description | Number of seconds the agent is full before triggering a flooding alert. |
| Default value | 15 |
| Allowed value | Any integer between 0 and 600. |
| **agent.warn\_level** | Description | Percentage of occupied capacity in agent buffer to trigger a warning alert. |
| Default value | 90 |
| Allowed value | Any integer between 1 and 100. |
| **agent.normal\_level** | Description | Percentage of occupied capacity in agent buffer to return to normal state. |
| Default value | 70 |
| Allowed value | Any integer between 0 and _agent.warn\_level - 1_. |
| **agent.min\_eps** | Description | Minimum events per second permitted in `<client_buffer>` configuration. |
| Default value | 50 |
| Allowed value | Any integer between 1 and 1000. |
| **agent.recv\_timeout** | Description | Maximum number of seconds to wait for server response from the TCP client socket. |
| Default value | 60 |
| Allowed value | Any integer between 1 and 600. |
| **agent.state\_interval** | Description | The interval between the updates of the agent status file in seconds. |
| Default value | 5 |
| Allowed values | 0: Disable status file |
| Any other integer between 1 and 86400 |
| **agent.debug** | Description | Run the Unix agent processes in debug mode. |
| Default value | 0 |
| Allowed value | 0: No debug output. |
| 1: Standard debug output. |
| 2: Verbose debug output. |
| **agent.remote\_conf** | Description | Apply or refuse remote configuration. |
| Default value | 1 |
| Allowed value | 0: Remote configuration is disabled. |
| 1: Remote configuration is enabled. |
| **agent.tcp\_keepidle** | Description | Time (in seconds) the connection needs to remain idle before TCP starts sending keepalive probes. |
| Default value | 60 |
| Allowed value | Any integer between 1 and 7200. |
| **agent.tcp\_keepintvl** | Description | Time (in seconds) between individual keepalive probes. |
| Default value | 15 |
| Allowed value | Any integer between 1 and 100. |
| **agent.tcp\_keepcnt** | Description | Maximum number of unanswered keepalive probes before the kernel drops the connection. |
| Default value | 4 |
| Allowed value | Any integer between 1 and 50. |
| **agent.send\_timeout** | Description | Maximum time (in seconds) that `send()` may block on the agent-to-manager TCP socket before timing out. |
| Default value | 30 |
| Allowed value | Any integer between 1 and 600. |

## Analysisd [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/reference/internal-options.html\#analysisd "Permalink to this headline")

|     |     |     |
| --- | --- | --- |
| **analysisd.default\_timeframe** | Description | Default rule time-frame. |
| Default value | 360 |
| Allowed value | Any integer between 60 and 360. |
| **analysisd.stats\_maxdiff** | Description | Stats maximum diff. |
| Default value | 999000 |
| Allowed value | Any integer between 10 and 999999. |
| **analysisd.stats\_mindiff** | Description | Stats minimum diff. |
| Default value | 1250 |
| Allowed value | Any integer between 10 and 999999. |
| **analysisd.stats\_percent\_diff** | Description | Stats percentage (how much to differ from average). |
| Default value | 150 |
| Allowed value | Any integer between 5 and 9999. |
| **analysisd.fts\_list\_size** | Description | FTS list size. |
| Default value | 32 |
| Allowed value | Any integer between 12 and 512. |
| **analysisd.fts\_min\_size\_for\_str** | Description | FTS minimum string size. |
| Default value | 14 |
| Allowed value | Any integer between 6 and 128. |
| **analysisd.log\_fw** | Description | Toggles firewall log on and off (at logs/firewall/firewall.log). |
| Default value | 1 |
| Allowed value | 0, 1 |
| **analysisd.decoder\_order\_size** | Description | Maximum number of fields in a decoder (order tag). |
| Default value | 256 |
| Allowed value | Any integer between 32 and 1024. |
| **analysisd.geoip\_jsonout** | Description | Toggle to turn on or off the output of GeoIP data in JSON alerts. |
| Default value | 0 |
| Allowed value | 0, 1 |
| **analysisd.label\_cache\_maxage** | Description | Number of in seconds without reloading labels in cache from agents. |
| Default value | 10 |
| Allowed value | Any integer between 0 and 60. |
| **analysisd.show\_hidden\_labels** | Description | Make hidden labels visible in alerts. |
| Default value | 0 |
| Allowed value | 0, 1 |
| **analysisd.rlimit\_nofile** | Description | Maximum number of file descriptors that Analysisd can open. |
| Default value | 458752 |
| Allowed value | Any integer between 1024 and 1048576. |
| **analysisd.debug** | Description | Debug level (manager installations). |
| Default value | 0 |
| Allowed value | 0: No debug output. |
| 1: Standard debug output. |
| 2: Verbose debug output. |
| **analysisd.min\_rotate\_interval** | Description | Minimum interval between log rotations.<br>Supersedes max\_output\_size option. |
| Default value | 600 |
| Allowed value | Any integer between 10 and 86400. |
| **analysisd.event\_threads** | Description | Number of event decoder threads. |
| Default value | 0 |
| Allowed value | 0: Sets the number of threads according to the number of CPU cores. |
| Any integer between 0 and 32. |
| **analysisd.syscheck\_threads** | Description | Number of syscheck event decoder threads. |
| Default value | 0 |
| Allowed value | 0: Sets the number of threads according to the number of CPU cores. |
| Any integer between 0 and 32. |
| **analysisd.syscollector\_threads** | Description | Number of Syscollector event decoder threads. |
| Default value | 0 |
| Allowed value | 0: Sets the number of threads according to the number of CPU cores. |
| Any integer between 0 and 32. |
| **analysisd.rootcheck\_threads** | Description | Number of Rootcheck event decoder threads. |
| Default value | 0 |
| Allowed value | 0: Sets the number of threads according to the number of CPU cores. |
| Any integer between 0 and 32. |
| **analysisd.sca\_threads** | Description | Number of SCA event decoder threads. |
| Default value | 0 |
| Allowed value | 0: Sets the number of threads according to the number of CPU cores. |
| Any integer between 0 and 32. |
| **analysisd.hostinfo\_threads** | Description | Number of hostinfo event decoder threads. |
| Default value | 0 |
| Allowed value | 0: Sets the number of threads according to the number of CPU cores. |
| Any integer between 0 and 32. |
| **analysisd.rule\_matching\_threads** | Description | Number of rule matching threads. |
| Default value | 0 |
| Allowed value | 0: Sets the number of threads according to the number of CPU cores. |
| Any integer between 0 and 32. |
| **analysisd.dbsync\_threads** | Description | Number of database synchronization dispatcher threads. |
| Default value | 0 |
| Allowed value | 0: Sets the number of threads according to the number of CPU cores. |
| Any integer between 0 and 32. |
| **analysisd.winevt\_threads** | Description | Number of Windows event decoder threads. |
| Default value | 0 |
| Allowed value | 0: Sets the number of threads according to the number of CPU cores. |
| Any integer between 0 and 32. |
| **analysisd.decode\_event\_queue\_size** | Description | Sets the decode event queue size. |
| Default value | 16384 |
| Allowed value | Any integer between 128 and 2000000. |
| **analysisd.decode\_syscheck\_queue\_size** | Description | Sets the decode Syscheck queue size. |
| Default value | 16384 |
| Allowed value | Any integer between 128 and 2000000. |
| **analysisd.decode\_syscollector\_queue\_size** | Description | Sets the decode Syscollector queue size. |
| Default value | 16384 |
| Allowed value | Any integer between 128 and 2000000. |
| **analysisd.decode\_rootcheck\_queue\_size** | Description | Sets the decode Rootcheck queue size. |
| Default value | 16384 |
| Allowed value | Any integer between 128 and 2000000. |
| **analysisd.decode\_sca\_queue\_size** | Description | Sets the decode SCA queue size. |
| Default value | 16384 |
| Allowed value | Any integer between 128 and 2000000. |
| **analysisd.decode\_hostinfo\_queue\_size** | Description | Sets the decode hostinfo queue size. |
| Default value | 16384 |
| Allowed value | Any integer between 128 and 2000000. |
| **analysisd.decode\_output\_queue\_size** | Description | Sets the decode output queue size. |
| Default value | 16384 |
| Allowed value | Any integer between 128 and 2000000. |
| **analysisd.decode\_winevt\_queue\_size** | Description | Sets the Windows event decode queue size. |
| Default value | 16384 |
| Allowed value | Any integer between 128 and 2000000. |
| **analysisd.archives\_queue\_size** | Description | Sets the archives log queue size. |
| Default value | 16384 |
| Allowed value | Any integer between 128 and 2000000. |
| **analysisd.statistical\_queue\_size** | Description | Sets the statistical log queue size. |
| Default value | 16384 |
| Allowed value | Any integer between 128 and 2000000. |
| **analysisd.alerts\_queue\_size** | Description | Sets the alerts log queue size. |
| Default value | 16384 |
| Allowed value | Any integer between 128 and 2000000. |
| **analysisd.firewall\_queue\_size** | Description | Sets the firewall log queue size. |
| Default value | 16384 |
| Allowed value | Any integer between 128 and 2000000. |
| **analysisd.fts\_queue\_size** | Description | Sets the fts log queue size. |
| Default value | 16384 |
| Allowed value | Any integer between 128 and 2000000. |
| **analysisd.dbsync\_queue\_size** | Description | Sets the database synchronization message queue size. |
| Default value | 16384 |
| Allowed value | Any integer between 128 and 2000000. |
| **analysisd.upgrade\_queue\_size** | Description | Sets the upgrade message queue size. |
| Default value | 16384 |
| Allowed value | Any integer between 128 and 2000000. |
| **analysisd.state\_interval** | Description | Sets the Analysisd interval for updating the state file in seconds. |
| Default value | 5 |
| Allowed value | Any integer between 0 and 86400. |

## Authd [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/reference/internal-options.html\#authd "Permalink to this headline")

|     |     |     |
| --- | --- | --- |
| **authd.debug** | Description | Debug level. |
| Default value | 0 |
| Allowed value | 0: No debug output |
| 1: Standard debug output |
| 2: Verbose debug output |
| **auth.timeout\_seconds** | Description | Network timeout to automatically close connections (second part). |
| Default value | 1 |
| Allowed value | Any integer between 1 and 2147483647. |
| **auth.timeout\_microseconds** | Description | Network timeout to automatically close connections (microsecond part). |
| Default value | 0 |
| Allowed value | Any integer between 0 and 999999. |

## DBD [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/reference/internal-options.html\#dbd "Permalink to this headline")

|     |     |     |
| --- | --- | --- |
| **dbd.reconnect\_attempts** | Description | Number of times wazuh-dbd will attempt to reconnect to the database. |
| Default value | 10 |
| Allowed value | Any integer between 1 and 9999. |

## Execd [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/reference/internal-options.html\#execd "Permalink to this headline")

|     |     |     |
| --- | --- | --- |
| **execd.request\_timeout** | Description | Timeout in seconds to execute remote requests. |
| Default Value | 60 |
| Allowed Value | Any integer between 1 and 3600. |
| **execd.max\_restart\_lock** | Description | Maximum timeout that the agent cannot restart while updating. |
| Default Value | 600 |
| Allowed Value | Any integer between 0 and 3600. |
| **execd.debug** | Description | Debug level |
| Default value | 0 |
| Allowed value | 0: No debug output |
| 1: Standard debug output |
| 2: Verbose debug output |

## Integrator [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/reference/internal-options.html\#integrator "Permalink to this headline")

|     |     |     |
| --- | --- | --- |
| **integrator.debug** | Description | Debug level. |
| Default value | 0 |
| Allowed value | 0: No debug output |
| 1: Standard debug output |
| 2: Verbose debug output |

## Logcollector [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/reference/internal-options.html\#logcollector "Permalink to this headline")

|     |     |     |
| --- | --- | --- |
| **logcollector.loop\_timeout** | Description | File polling interval. |
| Default value | 2 |
| Allowed value | Any integer between 1 and 120 |
| **logcollector.open\_attempts** | Description | Number of attempts to open a log file. The value 0 means that the number<br>of attempts is infinite. |
| Default value | 8 |
| Allowed value | Any integer between 0 and 998 |
| **logcollector.remote\_commands** | Description | Toggles Logcollector to accept remote commands from the manager or not. |
| Default value | 0 |
| Allowed value | 0: Disable remote commands |
| 1: Enable remote commands |
| **logcollector.vcheck\_files** | Description | File checking interval, in seconds. |
| Default value | 64 |
| Allowed value | Any integer between 0 and 1024 |
| **logcollector.max\_lines** | Description | Maximum number of logs read from the same file in each iteration. |
| Default value | 10000 |
| Allowed value | Any integer between 100 and 100000 |
| **logcollector.sample\_log\_length** | Description | Sample log length limit for errors about large input logs. |
| Default value | 64 |
| Allowed value | Any integer between 1 and 4096 |
| **logcollector.debug** | Description | Debug level (used in manager or Unix agent installations) |
| Default value | 0 |
| Allowed value | 0: No debug output |
| 1: Standard debug output |
| 2: Verbose debug output |
| **logcollector.input\_threads** | Description | Number of input threads reading files |
| Default value | 4 |
| Allowed value | Any integer between 1 and 128 |
| **logcollector.queue\_size** | Description | Queue size for each type of socket |
| Default value | 1024 |
| Allowed value | Any integer between 128 and 220000 |
| **logcollector.max\_files** | Description | Maximum number of files to be monitored |
| Default value | 1000 |
| Allowed value | Any integer between 1 and 100000 |
| **logcollector.sock\_fail\_time** | Description | Time to reattempt a socket connection after a failure, in seconds. |
| Default value | 300 |
| Allowed value | Any integer between 1 and 3600 |
| **logcollector.rlimit\_nofile** | Description | Maximum number of file descriptors that Logcollector can open.<br>This value must be **greater than or equal to**<br>( _logcollector.max\_files_ \+ 100). |
| Default value | 1100 |
| Allowed value | Any integer between 1024 and 1048576. |
| **logcollector.force\_reload** | Description | Force file handler reloading: close and reopen monitored files. |
| Default value | 0 |
| Allowed value | 0: Disabled |
| 1: Enabled |
| **logcollector.reload\_interval** | Description | File reloading interval, in seconds.<br>This parameter only applies if `logcollector.force_reload`<br>is set to `1`. |
| Default value | 64 |
| Allowed value | Any integer between 1 and 86400. |
| **logcollector.reload\_delay** | Description | File reloading delay (between close and open), in milliseconds.<br>This parameter only applies if `logcollector.force_reload`<br>is set to `1`. |
| Default value | 1000 |
| Allowed value | Any integer between 0 and 30000. |
| **logcollector.exclude\_files\_interval** | Description | Excluded files refresh interval, in seconds |
| Default value | 86400 |
| Allowed value | Any integer between 1 and 172800 |
| **logcollector.state\_interval** | Description | Statistics generation interval, in seconds |
| Default value | 60 |
| Allowed values | 0: Disable statistics file generation. Statistics information will continue<br>to be available through the API |
| Any other integer between 1 and 3600. |
| **logcollector.ip\_update\_interval** | Description | IP update interval, in seconds. This specifies how often the system<br>IP is obtained when the<br>[out\_format](https://documentation.wazuh.com/current/user-manual/reference/ossec-conf/localfile.html#ossec-localfile-out-format) option is used. |
| Default value | 60 |
| Allowed values | 0: Disable. Host IP address collection is disabled. The agent doesn't<br>periodically obtain the system IP address. |
| Any other integer between 1 and 3600.<br>**Warning:** Systems with extensive routing tables<br>can suffer from high CPU usage. |

## Maild [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/reference/internal-options.html\#maild "Permalink to this headline")

|     |     |     |
| --- | --- | --- |
| **maild.strict\_checking** | Description | Toggle to enable or disable strict checking. |
| Default value | 1 |
| Allowed value | 0, 1 |
| **maild.grouping** | Description | Toggle to enable or disable grouping of alerts into a single email. |
| Default value | 1 |
| Allowed value | 0, 1 |
| **maild.full\_subject** | Description | Toggle to enable or disable full subject in alert emails. |
| Default value | 0 |
| Allowed value | 0, 1 |
| **maild.geoip** | Description | Toggle to enable or disable GeoIP data in alert emails. |
| Default value | 1 |
| Allowed value | 0, 1 |

## Monitord [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/reference/internal-options.html\#monitord "Permalink to this headline")

|     |     |     |
| --- | --- | --- |
| **monitord.day\_wait** | Description | Number of seconds to wait before compressing or signing the files. |
| Default value | 10 |
| Allowed value | Any integer between 0 and 600. |
| **monitord.compress** | Description | Toggle to enable or disable log file compression. |
| Default value | 1 |
| Allowed value | 0, 1 |
| **monitord.sign** | Description | Toggle to enable or disable signing the log files. |
| Default value | 1 |
| Allowed value | 0, 1 |
| **monitord.monitor\_agents** | Description | Toggle to enable or disable monitoring of agents. |
| Default value | 1 |
| Allowed value | 0, 1 |
| **monitord.rotate\_log** | Description | Toggle to enable or disable daily rotation of internal logs. |
| Default value | 1 |
| Allowed value | 0, 1 |
| **monitord.keep\_log\_days** | Description | Number of days to keep rotated internal logs. |
| Default value | 31 |
| Allowed value | Any integer between 0 and 500. |
| **monitord.size\_rotate** | Description | Maximum size in Megabytes of internal logs to trigger rotation. |
| Default value | 512 |
| Allowed value | Any integer between 0 and 4096. |
| **monitord.daily\_rotations** | Description | Maximum number of rotations per day for internal logs. |
| Default value | 12 |
| Allowed value | Any integer between 1 and 256. |
| **monitord.debug** | Description | Debug level |
| Default value | 0 |
| Allowed value | 0: No debug output |
| 1: Standard debug output |
| 2: Verbose debug output |
| **monitord.delete\_old\_agents** | Description | Number of minutes before deleting an old disconnected agent.<br>This is a time-lapse after the agent is considered as<br>disconnected because of the<br>[disconnection time](https://documentation.wazuh.com/current/user-manual/reference/ossec-conf/global.html#reference-agents-disconnection-time). |
| Default value | 0 |
| Allowed value | Any integer between 0 and 9600. |

## Remoted [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/reference/internal-options.html\#remoted "Permalink to this headline")

|     |     |     |
| --- | --- | --- |
| **remoted.recv\_counter\_flush** | Description | Flush rate for the receive counter. |
| Default value | 128 |
| Allowed value | Any integer between 10 and 999999. |
| **remoted.comp\_average\_printout** | Description | Compression averages printout. |
| Default value | 19999 |
| Allowed value | Any integer between 10 and 999999. |
| **remoted.verify\_msg\_id** | Description | Toggle to enable or disable verification of msg id.<br>This setting doesn't work with multiple threads<br>(worker\_pool > 1). |
| Default value | 0 |
| Allowed value | 0, 1 |
| **remoted.pass\_empty\_keyfile** | Description | Toggle to enable or disable acceptance of empty client.keys. |
| Default value | 1 |
| Allowed value | 0, 1 |
| **remoted.sender\_pool** | Description | Number of parallel threads to send the shared file. |
| Default Value | 8 |
| Allowed Value | Any integer between 1 and 64. |
| **remoted.request\_pool** | Description | Limit of parallel threads to dispatch requests. |
| Default Value | 1024 |
| Allowed Value | Any integer between 1 and 4096. |
| **remoted.request\_timeout** | Description | Time (in seconds) the remote request listener rejects a<br>new request. |
| Default Value | 10 |
| Allowed Value | Any integer between 1 and 600. |
| **remoted.response\_timeout** | Description | Time (in seconds) the remote request listener rejects a<br>request response. |
| Default Value | 60 |
| Allowed Value | Any integer between 1 and 3600. |
| **remoted.request\_rto\_sec** | Description | Re-transmission timeout in seconds for UDP. |
| Default Value | 1 |
| Allowed Value | Any integer between 0 and 60. |
| **remoted.request\_rto\_msec** | Description | Re-transmission timeout in milliseconds for UDP. |
| Default Value | 0 |
| Allowed Value | Any integer between 0 and 999. |
| **remoted.max\_attempts** | Description | Maximum number of sending attempts. |
| Default Value | 4 |
| Allowed Value | Any integer between 1 and 16. |
| **remoted.merge\_shared** | Description | Merge shared configuration to be broadcast to agents. |
| Default Value | 1 (Enabled) |
| Allowed Value | 1 (Enabled), 0 (Disabled) |
| **remoted.disk\_storage** | Description | Store the temporary shared configuration file on disk. |
| Default Value | 0 (No, store in memory) |
| Allowed Value | 1 (Yes, store on disk), 0 (No, store in memory) |
| **remoted.shared\_reload** | Description | Number of seconds between reloading of shared files. |
| Default Value | 10 |
| Allowed Value | Any integer between 1 and 18000. |
| **remoted.rlimit\_nofile** | Description | Maximum number of file descriptors that Remoted can open. |
| Default value | 16384 |
| Allowed value | Any integer between 1024 and 1048576. |
| **remoted.recv\_timeout** | Description | Maximum number of seconds to wait for client response in TCP. |
| Default value | 1 |
| Allowed value | Any integer between 1 and 60. |
| **remoted.debug** | Description | Debug level (manager installation) |
| Default value | 0 |
| Allowed value | 0: No debug output. |
| 1: Standard debug output. |
| 2: Verbose debug output. |
| **remoted.keyupdate\_interval** | Description | Keys file reloading latency (seconds) |
| Default value | 10 |
| Allowed value | Any integer between 1 and 3600 |
| **remoted.worker\_pool** | Description | Number of threads that process the payload reception |
| Default value | 4 |
| Allowed value | Any integer between 1 and 16 |
| **remoted.state\_interval** | Description | Interval between the updates of the status file in seconds. |
| Default value | 5 |
| Allowed values | 0: Disable status file |
| Any other integer between 1 and 86400 |
| **remoted.guess\_agent\_group** | Description | Toggle to enable or disable the guessing of the group to<br>which the agent belongs when registering it again.<br>Note<br>Since version 4.4.0, in a cluster architecture,<br>this setting only applies to the master node. |
| Default value | 0 |
| Allowed values | 0, 1 |
| **remoted.receive\_chunk** | Description | Reception buffer size for TCP (bytes).<br>Amount of data that Remoted can receive per operation. |
| Default value | 4096 |
| Allowed value | Any other integer between 1024 and 16384.<br>Powers of two are suggested. |
| **remoted.send\_chunk** | Description | Send buffer size for TCP (bytes).<br>Amount of data that Remoted can send per operation. |
| Default value | 4096 |
| Allowed value | Any other integer between 512 and 16384.<br>Powers of two are suggested. |
| **remoted.send\_buffer\_size** | Description | Send queue size for TCP (bytes).<br>Amount of data that Remoted can queue to send<br>(one queue per agent). |
| Default value | 131072 |
| Allowed value | Any other integer between 65536 and 1048576.<br>Powers of two are suggested. |
| **remoted.ctrl\_msg\_queue\_size** | Description | Maximum number of control messages that can be queued for<br>processing. When the queue reaches this limit, backpressure<br>is applied to prevent memory exhaustion. |
| Default value | 16384 |
| Allowed value | Any integer between 1024 and 1048576. |
| **remoted.send\_timeout\_to\_retry** | Description | Maximum number of seconds to wait before retrying to<br>queue a packet to send in TCP. |
| Default value | 1 |
| Allowed value | Any integer between 1 and 60. |
| **remoted.buffer\_relax** | Description | Method for memory deallocation after accepting input data.<br>This option applies in TCP mode only. |
| Default value | 1 |
| Allowed values | 0: Keep the memory for each TCP session. |
| 1: Shrink memory back to `receive_chunk`. |
| 2: Fully deallocate memory after usage. |
| **remoted.tcp\_keepidle** | Description | Time (in seconds) the connection needs to remain idle<br>before TCP starts sending keepalive probes. |
| Default value | 30 |
| Allowed value | Any integer between 1 and 7200. |
| **remoted.tcp\_keepintvl** | Description | The time (in seconds) between individual keepalive probes. |
| Default value | 10 |
| Allowed value | Any integer between 1 and 100. |
| **remoted.tcp\_keepcnt** | Description | Maximum number of keepalive probes TCP should send before<br>dropping the connection. |
| Default value | 3 |
| Allowed value | Any integer between 1 and 50. |

## Syscheck [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/reference/internal-options.html\#syscheck "Permalink to this headline")

|     |     |     |
| --- | --- | --- |
| **syscheck.rt\_delay** | Description | Time in milliseconds for delay between alerts in real-time. |
| Default value | 10 |
| Allowed value | Any integer between 1 and 1000 |
| **syscheck.max\_fd\_win\_rt** | Description | Maximum numbers of directories can be configured in ossec.conf for Windows<br>in realtime and whodata mode. |
| Default value | 256 |
| Allowed value | Any integer between 1 and 1024 |
| **syscheck.max\_audit\_entries** | Description | Maximum number of directories monitored for who-data on Linux. |
| Default value | 256 |
| Allowed value | Any integer between 1 and 4096 |
| **syscheck.default\_max\_depth** | Description | Maximum level of recursion allowed while reading directories. |
| Default value | 256 |
| Allowed value | Any integer between 1 and 320 |
| **syscheck.symlink\_scan\_interval** | Description | Check interval of the symbolic links configured in the directories section. |
| Default value | 600 |
| Allowed value | Any integer between 1 and 2592000 |
| **syscheck.file\_max\_size** | Description | Maximum file size for calculating integrity hashes (in mebibytes). |
| Default value | 1024 |
| Allowed value | 0: Unlimited |
| Any integer between 0 and 4095 |
| **syscheck.debug** | Description | Debug level (used in manager and Unix agent installations). |
| Default value | 0 |
| Allowed value | 0: No debug output |
| 1: Standard debug output |
| 2: Verbose debug output |

## Rootcheck [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/reference/internal-options.html\#rootcheck "Permalink to this headline")

|     |     |     |
| --- | --- | --- |
| **rootcheck.sleep** | Description | Number of milliseconds to sleep after reading one PID or suspicious port. |
| Default value | 50 |
| Allowed values | Any integer between 0 and 1000. |

## Security Configuration Assessment [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/reference/internal-options.html\#security-configuration-assessment "Permalink to this headline")

|     |     |     |
| --- | --- | --- |
| **sca.request\_db\_interval** | Description | In case of integrity fail, this is the maximum interval (minutes) to resend the scan information to the manager. |
| Default value | 5 |
| Allowed values | Any integer between 1 and 60. |
| **sca.remote\_commands** | Description | Enable the execution of commands in policy files received from the manager (Files in etc/shared). |
| Default value | 0 |
| Allowed values | 1 (enabled) or 0 (disabled). |
| **sca.commands\_timeout** | Description | Timeout for the commands execution. |
| Default value | 30 (seconds) |
| Allowed values | Any integer between 1 and 300. |

## Vulnerability Detection [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/reference/internal-options.html\#vulnerability-detection "Permalink to this headline")

|     |     |     |
| --- | --- | --- |
| **vulnerability-detection.translation\_lru\_size** | Description | LRU cache size assigned for package translation process (in number of elements). |
| Default value | 2048 |
| Allowed values | Any integer between 1 and 100000 |
| **vulnerability-detection.osdata\_lru\_size** | Description | LRU cache size assigned for agents' OS data (in number of elements). |
| Default value | 1000 |
| Allowed values | Any integer between 1 and 100000 |
| **vulnerability-detection.remediation\_lru\_size** | Description | LRU cache size assigned for vulnerability remediation (in number of elements). |
| Default value | 2048 |
| Allowed values | Any integer between 1 and 100000 |

## Wazuh [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/reference/internal-options.html\#wazuh "Permalink to this headline")

|     |     |     |
| --- | --- | --- |
| **wazuh.thread\_stack\_size** | Description | Stack size assigned for child threads created in Wazuh (in KiB). |
| Default value | 8192 |
| Allowed values | Any integer between 2048 and 65536 |

## Wazuh Clusterd [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/reference/internal-options.html\#wazuh-clusterd "Permalink to this headline")

|     |     |     |
| --- | --- | --- |
| **wazuh\_clusterd.debug** | Description | Debug level. |
| Default value | 0 |
| Allowed value | 0: No debug output. |
| 1: Standard debug output. |
| 2: Verbose debug output. |

## Wazuh Database [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/reference/internal-options.html\#wazuh-database "Permalink to this headline")

The Wazuh Database Synchronization Module starts automatically on the server and local profiles and requires no configuration, however, some optional settings are available.

The module uses _inotify_ from Linux to monitor changes to every log file in real-time. Databases will be updated as soon as possible when a change is detected. **If inotify is not supported**, (for example, on operating systems other than Linux) every log file will be scanned continuously, looking for changes, with a default delay of one minute between scans.

### How to disable the module [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/reference/internal-options.html\#how-to-disable-the-module "Permalink to this headline")

To disable the Wazuh Database Synchronization Module, the sync directives must be set to 0 in the `etc/local_internal_options.conf` file as shown below:

Copied to clipboard

```
wazuh_database.sync_agents=0
```

Once these settings have been adjusted, the file must be saved followed by a restart of Wazuh. With the above settings, the Database Synchronization Module will not be loaded when Wazuh starts.

|     |     |     |
| --- | --- | --- |
| **wazuh\_database.sync\_agents** | Description | Toggles synchronization of agent database with client.keys on or off. |
| Default value | 1 |
| Allowed value | 0, 1 |
| **wazuh\_database.real\_time** | Description | Toggles synchronization of data in real-time (supported on Linux only) on and off. |
| Default value | 1 |
| Allowed value | 0, 1 |
| **wazuh\_database.interval** | Description | Interval to sleep between cycles. (Only used if real time sync is disabled). |
| Default value | 60 |
| Allowed value | Any integer between 0 and 86400 (seconds). |
| **wazuh\_database.max\_queued\_events** | Description | Maximum number of queued events (only used if _inotify_ is available). |
| Default value | 0 (use system default value). |
| Allowed value | Any integer between 0 and 2147483647. |

## Wazuh Modules [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/reference/internal-options.html\#wazuh-modules "Permalink to this headline")

|     |     |     |
| --- | --- | --- |
| **wazuh\_modules.task\_nice** | Description | Indicates the priority of the tasks. The lower the value, the higher the priority. |
| Default value | 10 |
| Allowed value | Any integer between -20 and 19. |
| **wazuh\_modules.rlimit\_nofile** | Description | Maximum number of file descriptor that Wazuh modules can open. |
| Default value | 8192 |
| Allowed value | Any integer between 1024 and 1048576 |
| **wazuh\_modules.max\_eps** | Description | Maximum number of events per second sent by all Wazuh Module. |
| Default value | 100 |
| Allowed value | Any integer between 1 and 1000 |
| **wazuh\_modules.kill\_timeout** | Description | Time for a process to quit before being killed during Modulesd exiting, in seconds. |
| Default value | 10 |
| Allowed value | 0: Kill immediately |
| Any integer between 1 and 3600 |
| **wazuh\_modules.debug** | Description | Debug level. |
| Default value | 0 |
| Allowed value | 0: No debug output. |
| 1: Standard debug output. |
| 2: Verbose debug output. |

## Wazuh Command [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/reference/internal-options.html\#wazuh-command "Permalink to this headline")

|     |     |     |
| --- | --- | --- |
| **wazuh\_command.remote\_commands** | Description | Toggles whether Command Module should accept commands defined in the shared configuration or not. |
| Default value | 0 |
| Allowed value | 0: Disable remote commands. |
| 1: Enable remote commands. |

## Wazuh-db [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/reference/internal-options.html\#wazuh-db "Permalink to this headline")

|     |     |     |
| --- | --- | --- |
| **wazuh\_db.worker\_pool\_size** | Description | Number of worker threads |
| Default value | 8 |
| Allowed value | Any integer between 1 and 32 |
| **wazuh\_db.open\_db\_limit** | Description | Maximum number of allowed open databases before closing |
| Default value | 64 |
| Allowed value | Any integer between 1 and 4096 |
| **wazuh\_db.rlimit\_nofile** | Description | Maximum number of file descriptors that Wazuh-DB can open. |
| Default value | 65536 |
| Allowed value | Any integer between 1024 and 1048576. |
| **wazuh\_db.commit\_time\_min** | Description | Minimum time margin before committing. |
| Default value | 10 |
| Allowed value | Any integer between 1 and 3600. |
| **wazuh\_db.commit\_time\_max** | Description | Maximum time margin before committing. |
| Default value | 60 |
| Allowed value | Any integer between 1 and 3600. |
| **wazuh\_db.max\_fragmentation** | Description | Maximum fragmentation allowed for a database. |
| Default value | 90 |
| Allowed value | Any integer between 0 and 100. |
| **wazuh\_db.fragmentation\_threshold** | Description | Indicates the allowed fragmentation threshold. |
| Default value | 75 |
| Allowed value | Any integer between 0 and 100. |
| **wazuh\_db.fragmentation\_delta** | Description | Indicates the allowed fragmentation difference between the last time<br>the vacuum was performed and the current measurement. |
| Default value | 5 |
| Allowed value | Any integer between 0 and 100. |
| **wazuh\_db.free\_pages\_percentage** | Description | Indicates the minimum percentage of free pages present in a database that<br>can trigger a vacuum. |
| Default value | 0 |
| Allowed value | Any integer between 0 and 99. |
| **wazuh\_db.check\_fragmentation\_interval** | Description | Interval for database fragmentation check, in seconds. |
| Default value | 7200 |
| Allowed value | Any integer between 1 and 30758400. |
| **wazuh\_db.debug** | Description | Debug level |
| Default value | 0 |
| Allowed value | 0: No debug output |
| 1: Standard debug output |
| 2: Verbose debug output |

## Wazuh-download [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/reference/internal-options.html\#wazuh-download "Permalink to this headline")

|     |     |     |
| --- | --- | --- |
| **wazuh\_download.enabled** | Description | Enable download module |
| Default value | 1 |
| Allowed value | 0: Disable download module. |
| 1: Enable download module. |

## Windows [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/reference/internal-options.html\#windows "Permalink to this headline")

|     |     |     |
| --- | --- | --- |
| **windows.debug** | Description | Debug level (used in windows agent installations). |
| Default value | 0 |
| Allowed value | 0: No debug output. |
| 1: Standard debug output. |
| 2: Verbose debug output. |

[Centralized configuration (agent.conf)](https://documentation.wazuh.com/current/user-manual/reference/centralized-configuration.html "Previous. Centralized configuration (agent.conf)") [Daemons](https://documentation.wazuh.com/current/user-manual/reference/daemons/index.html "Next. Daemons")

Close