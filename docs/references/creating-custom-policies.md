Source: https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html

Contact us

# Creating custom SCA policies [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html\#creating-custom-sca-policies "Permalink to this headline")

You need to consider the following four sections when creating custom policy files, although not all of them are required.

| Section | Required |
| --- | --- |
| policy | Yes |
| requirements | No |
| variables | No |
| checks | Yes |

Policy file sections [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html#id1 "Permalink to this headline")

An SCA policy looks like the following:

Copied to clipboard

```
# Security Configuration Assessment
# Audit for UNIX systems
# Copyright (C) 2015, Wazuh Inc.
#
# This program is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public
# License (version 2) as published by the FSF - Free Software
# Foundation

policy:
  id: "unix_audit"
  file: "sca_unix_audit.yml"
  name: "System audit for Unix based systems"
  description: "Guidance for establishing a secure configuration for Unix based systems."
  references:
    - https://www.ssh.com/ssh/

requirements:
  title: "Check that the SSH service and password-related files are present on the system"
  description: "Requirements for running the SCA scan against the Unix based systems policy."
  condition: any
  rules:
    - 'f:$sshd_file'
    - 'f:/etc/passwd'
    - 'f:/etc/shadow'

variables:
  $sshd_file: /etc/ssh/sshd_config
  $pam_d_files: /etc/pam.d/common-password,/etc/pam.d/password-auth,/etc/pam.d/system-auth,/etc/pam.d/system-auth-ac,/etc/pam.d/passwd

checks:
  - id: 3000
    title: "SSH Hardening: Port should not be 22"
    description: "The ssh daemon should not be listening on port 22 (the default value) for incoming connections."
    rationale: "Changing the default port you may reduce the number of successful attacks from zombie bots, an attacker or bot doing port-scanning can quickly identify your SSH port."
    remediation: "Change the Port option value in the sshd_config file."
    compliance:
      - pci_dss: ["2.2.4"]
      - nist_800_53: ["CM.1"]
    condition: all
    rules:
      - 'f:$sshd_file -> !r:^# && r:Port && !r:\s*\t*22$'

  - id: 3001
    title: "SSH Hardening: Protocol should be set to 2"
```

Note

If the `requirements` aren't satisfied for a specific policy file, the scan for that file won't start.

Each section has its fields as described in the tables [Policy section](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html#sca-policy-file-policy-section), [Requirements section](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html#sca-policy-file-requirements-section), [Variables section](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html#sca-policy-file-variables-section), and [Checks section](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html#sca-policy-file-checks-section).

| Field | Mandatory | Type | Allowed values | Description |
| --- | --- | --- | --- | --- |
| id | Yes | String | Any string | Policy ID |
| file | Yes | String | Any string | Policy filename |
| name | Yes | String | Any string | Policy title |
| description | Yes | String | Any string | Brief description |
| references | No | Array of strings | Any string (empty by default) | Links to references |
| regex\_type | No | String | "osregex" (default), "pcre2" | Policy regex engine |

Policy section [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html#id2 "Permalink to this headline")

| Field | Mandatory | Type | Allowed values |
| --- | --- | --- | --- |
| title | Yes | String | Any string |
| description | Yes | String | Any string |
| condition | Yes | String | Any string |
| rules | Yes | Array of strings | Any string |

Requirements section [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html#id3 "Permalink to this headline")

| Field | Mandatory | Type | Allowed values |
| --- | --- | --- | --- |
| variable\_name | Yes | Array of strings | Any string |

Variables section [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html#id4 "Permalink to this headline")

Note

The `id` field under `policy` and `checks` must be unique across policy files.

## Variables [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html\#variables "Permalink to this headline")

Variables are set in the variables section. Their names are preceded by `$`. For instance:

- `$list_of_files`: `/etc/ssh/sshd_config`, `/etc/sysctl.conf`, `/var/log/dmesg`

- `$list_of_folders`: `/etc`, `/var`, `/tmp`

- `$program_name`: `apache2`


Variables can be placed anywhere in the left part of the rule. Therefore, regarding the variables above, the following rules could be built:

Copied to clipboard

```
f:$list_of_files -> r:^Content to be found
c:systemctl is-enabled $program_name -> r:^enabled
```

There is no limit on the number of variables to add within a rule.

## Checks [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html\#checks "Permalink to this headline")

Checks are the core of an SCA policy, as they describe the scan to be performed in the endpoint. The checks contain fields that define what actions the agent should take to scan the endpoint, and how to evaluate the scan results. Each check is composed of several fields as described in the table below:

| Field | Mandatory | Type | Allowed values |
| --- | --- | --- | --- |
| id | Yes | Numeric | Any integer number |
| title | Yes | String | Any string |
| description | No | String | Any string |
| rationale | No | String | Any string |
| remediation | No | String | Any string |
| compliance | No | Array of arrays of strings | Any string |
| references | No | Array of strings | Any string |
| condition | Yes | String | all, any, none |
| rules | Yes | Array of strings | Any string |
| regex\_type | No | String | "pcre2" or "osregex" |

Checks section [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html#id5 "Permalink to this headline")

Check evaluation is governed by its rule result aggregation strategy, as set in its `condition` field, and the results of
the evaluation of its rules.

Note

If you set a `regex_type`, it overrides the regex engine type defined in the policy.

### Condition [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html\#condition "Permalink to this headline")

The result of each SCA check is governed by the conditions set in the `condition` field, and the results of the evaluation of its rules. The condition field specifies how rule results are aggregated in order to calculate the final value of a check. There are three options:

- `all`: The check is evaluated as **Passed** if all of its rules are satisfied and as **Failed** as soon as one rule is not satisfied.

- `any`: The check is evaluated as **Passed** as soon as any of its rules are satisfied.

- `none`: The check is evaluated as **Passed** if none of its rules are satisfied and as **Failed** as soon as one rule is satisfied.


There are certain situations in which the aforementioned aggregators are evaluated as **Not applicable**.

- `all`: If any rule returns **Not applicable**, and no rule returns **Failed**, the result is **Not applicable**.

- `any`: The check is evaluated as **Not applicable** if no rule is evaluated as **Passed** and any rule returns **Not applicable**.

- `none`: The check is evaluated as **Not applicable** if no rule is evaluated as **Passed** and any rule returns **Not applicable**.


| Condition \ Rule evaluation | Passed | Failed | Not applicable | Result |
| --- | --- | --- | --- | --- |
| `all` | yes | no | no | Passed |
| `all` | \* | no | yes | Not applicable |
| `all` | \* | yes | \* | Failed |
| `any` | yes | \* | \* | Passed |
| `any` | no | yes | no | Failed |
| `any` | no | \* | yes | Not applicable |
| `none` | yes | \* | \* | Failed |
| `none` | no | \* | yes | Not applicable |
| `none` | no | yes | no | Passed |

Condition / rule evaluation [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html#id6 "Permalink to this headline")

\\* This result does not affect the final result.

### Rules [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html\#rules "Permalink to this headline")

Rules can check for the existence of files, directories, registry keys and values, running processes, and recursively test for the existence of files inside directories. When it comes to content checking, they are able to check for file contents, recursively check for the contents of files inside directories, command output, and registry value data.

Abstractly, rules start with a location and a type of location that is the target of the test, followed by the actual test specification. Such tests fall into two categories: existence and content checks. The type of location is listed in the [Rule types](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html#rule-types) table below, and the location could be a file name, directory, process name, command, or a registry key.

There are five main types of rules as described below.

| Type | Character |
| --- | --- |
| File | `f` |
| Directory | `d` |
| Process | `p` |
| Commands | `c` |
| Registry (Windows Only) | `r` |

Rule types [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html#id7 "Permalink to this headline")

The operators for content checking are shown in the content comparison operators table below.

| Operation | Operator | Example |
| --- | --- | --- |
| Literal comparison, exact match | _by omission (the absence of an operator signifies a literal comparison or exact match)_ | `f:/file -> CONTENT` |
| [Lightweight Regular expression](https://documentation.wazuh.com/current/user-manual/ruleset/ruleset-xml-syntax/regex.html) match | `r:` | `f:/file -> r:REGEX` |
| Numeric comparison (integers) | `n:` | `f:/file -> n:REGEX_WITH_CAPTURE_GROUP compare <= VALUE` |

Content comparison operators [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html#id8 "Permalink to this headline")

The operators for numeric comparison are shown in the table below.

| Arithmetic relational operator | Operator | Example |
| --- | --- | --- |
| less than | `<` | `n:SomeProperty (\d) compare < 42` |
| less than or equal to | `<=` | `n:SomeProperty (\d) compare <= 42` |
| equal to | `==` | `n:SomeProperty (\d) compare == 42` |
| not equal to | `!=` | `n:SomeProperty (\d) compare != 42` |
| greater than or equal to | `>=` | `n:SomeProperty (\d) compare >= 42` |
| greater than | `>` | `n:SomeProperty (\d) compare > 42` |

Numeric comparison operators [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html#id9 "Permalink to this headline")

You can place `not` at the beginning of a rule to negate it. For example:

Copied to clipboard

```
not f:/some_file -> some_text
```

The SCA rule above fails if `some_text` is found within the contents of `some_file`.

By combining the aforementioned rule types and operators, both existence and content checking can be performed.

Note

- **Process** rules only allow existence checks.

- **Command** rules only allow content (output) checks.


#### Existence checking rules [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html\#existence-checking-rules "Permalink to this headline")

Existence checks are created by setting rules without a content operator.The general form is as follows:

Copied to clipboard

```
RULE_TYPE:target
```

Examples of existence checks:

- `f:/etc/sshd_config` checks the existence of `/etc/sshd_config` file.

- `d:/etc` checks the existence of the `/etc` directory.

- `not p:sshd` tests the presence of processes called `sshd` and fails if one is found.

- `r:HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Lsa` checks for the existence of the `HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Lsa` key.

- `r:HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Lsa -> LimitBlankPasswordUse` checks for the existence of _LimitBlankPasswordUse_ value in the key.


#### Content checking rules [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html\#content-checking-rules "Permalink to this headline")

The general form of a rule testing for contents is as follows:

Copied to clipboard

```
RULE_TYPE:target -> CONTENT_OPERATOR:value
```

Note

- The context of a content check is limited to a **line**.

- It is **mandatory** to respect the spaces around the `->` and `compare` separators.

- If the **target** of a rule that checks for contents does not exist, the result will be `Not applicable` as it could not be checked.


Content check operator results can be negated by adding a `!` before then, for example:

Copied to clipboard

```
f:/etc/ssh_config -> !r:PermitRootLogin
```

Note

Be careful when negating content operators as that makes them evaluate as **Passed** for anything that does not match with the check specified. For example, rule `f:/etc/ssh_config -> !r:PermitRootLogin` is evaluated as Passed if it finds any line that does not contain `PermitRootLogin`.

Content check operators can be chained using the operator `&&` (AND) as follows:

Copied to clipboard

```
f:/etc/ssh_config -> !r:^# && r:Protocol && r:2
```

This rule reads as **Pass** if there's a line whose first character is not `#` and contains `Protocol` and `2`.

Note

- It is mandatory to respect the spaces around the `&&` operator.

- There's no particular order of evaluation between tests chained using the `&&` operator.


Examples of content checks:

- `c:systemctl is-enabled cups -> r:^enabled` checks that the output of the command contains a line starting with enabled.

- `f:$sshd_file -> n:^\s*MaxAuthTries\s*\t*(\d+) compare <= 4` checks that MaxAuthTries is less or equal to 4.

- `r:HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Lsa -> LimitBlankPasswordUse -> 1` checks that the value of _LimitBlankPasswordUse_ is 1.


#### Examples [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html\#examples "Permalink to this headline")

The following sections cover each rule type, illustrating them with several examples. It is also recommended to check the actual policies and, for minimalistic although complete examples, the [SCA test suite policies](https://github.com/wazuh/wazuh-qa/tree/master/tests/legacy/test_sca/test_basic_usage/data).

##### Rule syntax for files [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html\#rule-syntax-for-files "Permalink to this headline")

- Check that a file exists: `f:/path/to/file`

- Check that a file does not exist: `not f:/path/to/file`

- Check file contains (whole line literal match): `f:/path/to/file -> content`

- Check file contents against regex: `f:/path/to/file -> r:REGEX`

- Check a numeric value: `f:/path/to/file -> n:REGEX(\d+) compare <= Number`


##### Rule syntax for directories [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html\#rule-syntax-for-directories "Permalink to this headline")

- Check if a directory exists: `d:/path/to/directory`

- Check if a directory contains a file: `d:/path/to/directory -> file`

- Check if a directory contains files that match a regex: `d:/path/to/directory -> r:^files`

- Check files matching `file_name` for content: `d:/path/to/directory -> file_name -> content`


##### Rule syntax for processes [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html\#rule-syntax-for-processes "Permalink to this headline")

- Check if a process is running `p:process_name`

- Check if a process is **not** running `not p:process_name`


##### Rule syntax for commands [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html\#rule-syntax-for-commands "Permalink to this headline")

- Check the output of a command `c:command -> output`

- Check the output of a command using regex `c:command -> r:REGEX`

- Check a numeric value `c:command -> n:REGEX_WITH_A_CAPTURE_GROUP compare >= number`


##### Rule syntax for Windows Registry [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html\#rule-syntax-for-windows-registry "Permalink to this headline")

- Check if a registry exists `r:path/to/registry`

- Check if a registry key exists `r:path/to/registry -> key`

- Check registry key contents `r:path/to/registry -> key -> content`


##### Composite rules [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html\#composite-rules "Permalink to this headline")

- Check if there is a line that does not begin with `#` and contains `Port 22``f:/etc/ssh/sshd_config -> !r:^# && r:Port\.+22`

- Check if there is no line that does not begin with `#` and contains `Port 22``not f:/etc/ssh/sshd_config -> !r:^# && r:Port\.+22`


##### Other examples [Permalink to this headline](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/creating-custom-policies.html\#other-examples "Permalink to this headline")

- Check for file contents, whole line match: `f:/proc/sys/net/ipv4/ip_forward -> 1`

- Check if a file exists: `f:/proc/sys/net/ipv4/ip_forward`

- Check if a process is running: `p:avahi-daemon`

- Check value of registry: `r:HKEY_LOCAL_MACHINE\System\CurrentControlSet\Services\Netlogon\Parameters -> MaximumPasswordAge -> 0`

- Check if a directory contains files: `d:/home -> ^.mysql_history$`

- Check if a directory exists: `d:/etc/mysql`

- Check the running configuration of sshd for the maximum authentication tries allowed: `c:sshd -T -> !r:^\s*maxauthtries\s+4\s*$`

- Check if root is the only account with UID 0: `f:/etc/passwd -> !r:^# && !r:^root: && r:^\w+:\w+:0:`


[Available SCA policies](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/available-sca-policies.html "Previous. Available SCA policies") [Use cases](https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/use-cases.html "Next. Use cases")

Close