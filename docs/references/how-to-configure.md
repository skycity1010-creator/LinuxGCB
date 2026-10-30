Source: https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/how-to-configure.html

Contact us

# How to configure SCA [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/how-to-configure.html\#how-to-configure-sca "Permalink to this headline")

Wazuh agents include the appropriate policies for their particular operating system during installation. For the full list of officially supported policy files, see the table [Available SCA policies](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/available-sca-policies.html#id1). These policies are included with the Wazuh server installation so that they can be easily enabled.

For a detailed description of the various configuration parameters of SCA, please check the [SCA reference](https://documentation.wazuh.com/current/user-manual/reference/ossec-conf/sca.html#reference-sec-config-assessment).

## Enabling and disabling policies [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/how-to-configure.html\#enabling-and-disabling-policies "Permalink to this headline")

By default, the Wazuh agent scans every policy (`.yaml` or `.yml` file) in its ruleset folder:

- Linux and Unix-based agents: `/var/ossec/ruleset/sca`.

- Windows agents: `C:\Program Files (x86)\ossec-agent\ruleset\sca`.

- macOS agents: `/Library/Ossec/ruleset/sca`.


Note

Installations and updates don't preserve the contents of these default ruleset folders. Place your policies under an alternative folder if you want to modify or add new ones.

There are two ways to disable policies on the Wazuh agent. The simplest method is to rename the policy file with an extension other than `.yaml` or `.yml`.

Alternatively, disable a policy in the Wazuh agent `ossec.conf` file by setting the `enabled` attribute to `no`.

To disable a policy included with the Wazuh agent, specify its path relative to the Wazuh installation directory:

Copied to clipboard

```
<sca>
  <policies>
    <policy enabled="no">ruleset/sca/<POLICY_FILE_TO_DISABLE></policy>
  </policies>
</sca>
```

For a policy distributed through centralized configuration, use its path in the `etc/shared` directory:

Copied to clipboard

```
<sca>
  <policies>
    <policy enabled="no">etc/shared/<POLICY_FILE_TO_DISABLE></policy>
  </policies>
</sca>
```

You can also specify an absolute path to the policy file.

Restart the Wazuh agent to apply the change:

SystemdSysV init

Copied to clipboard

```
# systemctl restart wazuh-agent
```

## How to share policy files and configuration with the Wazuh agents [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/how-to-configure.html\#how-to-share-policy-files-and-configuration-with-the-wazuh-agents "Permalink to this headline")

As described in the [centralized configuration](https://documentation.wazuh.com/current/user-manual/reference/centralized-configuration.html) section, the Wazuh server can push files and configurations to connected Wazuh agents.

You can enable this feature to push policy files to the Wazuh agents in defined groups. By default, every Wazuh agent belongs to the `default` group, which is used here as an example:

1. Edit the Wazuh agent `local_internal_options.conf` file to allow the execution of commands in SCA policies sent from the Wazuh server:



LinuxWindowsmacOS





Copied to clipboard



```
# echo "sca.remote_commands=1" >> /var/ossec/etc/local_internal_options.conf
```











Note



By enabling remote command execution, the Wazuh server can execute commands on the monitored endpoint. Remote commands are disabled by default as a security measure, helping reduce the attack surface if the Wazuh server is compromised.



You do not need to enable remote commands if you add the policy files to each agent without using Wazuh to push them. For example, you can manually create the policy file directly on the monitored endpoint, or use `scp` to copy the policy file to the monitored endpoint.

2. On the Wazuh server, place a new policy file in the `/var/ossec/etc/shared/default` folder and change its ownership. Replace `<NEW_POLICY_FILE>` with your policy name.


> Copied to clipboard
>
> ```
> # chown wazuh:wazuh /var/ossec/etc/shared/default/<NEW_POLICY_FILE>
> ```

3. Add the following configuration block to the Wazuh server `/var/ossec/etc/shared/default/agent.conf` file to configure the new policy file in the Wazuh agent:


> Copied to clipboard
>
> ```
> <agent_config>
>   <!-- Shared agent configuration here -->
>   <sca>
>     <policies>
>         <policy>etc/shared/<NEW_POLICY_FILE></policy>
>     </policies>
>   </sca>
> </agent_config>
> ```


All files remotely pushed from the Wazuh server are saved in the `/<WAZUH_HOME_DIRECTORY>/etc/shared/` directory on the agent endpoints regardless of the group they belong to. We specify the relative file path of the policy in the configuration because the full file path could differ depending on the operating system of the monitored endpoint.


The new `<sca>` block in the Wazuh server `/var/ossec/etc/shared/default/agent.conf` file is merged with the `<sca>` block on the Wazuh agent side, and the new configuration is added.

[How SCA works](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/how-it-works.html "Previous. How SCA works") [Available SCA policies](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/available-sca-policies.html "Next. Available SCA policies")

Close