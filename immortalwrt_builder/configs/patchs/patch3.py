# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

from immortalwrt_builder.builder.core.patch.interface import PatchContext


def patch(context: PatchContext) -> None:
    """Post-feeds/optimization patch: configure sysctl kernel parameters, rc.local, and irqbalance."""
    print("Executing patch3: tuning kernel network parameters, rc.local, and services...", flush=True)

    # 1. Sysctl network optimizations
    sysctl_conf = """
vm.swappiness=10
vm.vfs_cache_pressure=50

fs.nr_open=1200000
fs.file-max=200000

# Enable TCP SYN cookies
net.ipv4.tcp_syncookies=1

# Increase maximum number of connections
net.core.somaxconn=65535

# Increase maximum number of queued packets
net.core.netdev_max_backlog=1000

# Increase buffer sizes for TCP
net.core.rmem_default=65536
net.core.wmem_default=65536
net.core.rmem_max=16777216
net.core.wmem_max=16777216

# TCP settings
net.ipv4.tcp_max_syn_backlog=4096
net.ipv4.tcp_synack_retries=1
net.ipv4.tcp_keepalive_time=1800
net.ipv4.tcp_keepalive_intvl=15
net.ipv4.tcp_keepalive_probes=5
net.ipv4.tcp_fin_timeout=10
net.ipv4.tcp_max_orphans=65536
net.ipv4.tcp_mem=50576 64768 98152
net.ipv4.tcp_rmem=4096 87380 16777216
net.ipv4.tcp_wmem=4096 65536 16777216
net.ipv4.tcp_orphan_retries=0
net.ipv4.tcp_no_metrics_save=1
net.ipv4.tcp_window_scaling=1
net.ipv4.tcp_timestamps=1
net.ipv4.tcp_sack=1
net.ipv4.tcp_rfc1337=1
"""
    context.append_text("package/base-files/files/etc/sysctl.conf", sysctl_conf)

    # 2. Custom rc.local network queue configuration
    rc_local_content = """# Put your custom commands here that should be executed once
# the system init finished. By default this file does nothing.
#!/bin/sh

# Set RX and TX queue limits for supported interfaces
for iface in br-lan eth0 eth1 rax0 ra0; do
\tif [ -d /sys/class/net/$iface/queues/rx-0 ]; then
\t\tif [ -f /sys/class/net/$iface/queues/rx-0/rps_flow_cnt ]; then
\t\t\techo 1024 > /sys/class/net/$iface/queues/rx-0/rps_flow_cnt
\t\tfi
\tfi

\tif [ -d /sys/class/net/$iface/queues/tx-0 ]; then
\t\tif [ -d /sys/class/net/$iface/queues/tx-0/byte_queue_limits ]; then
\t\t\techo 1024 > /sys/class/net/$iface/queues/tx-0/byte_queue_limits/limit
\t\t\techo 2048 > /sys/class/net/$iface/queues/tx-0/byte_queue_limits/limit_max
\t\t\techo 512 > /sys/class/net/$iface/queues/tx-0/byte_queue_limits/limit_min
\t\tfi
\tfi
done

exit 0
"""
    context.write_text("package/base-files/files/etc/rc.local", rc_local_content)

    # 3. Enable irqbalance
    irq_conf = "package/feeds/packages/irqbalance/files/irqbalance.config"
    context.replace_text(irq_conf, "option enabled '0'", "option enabled '1'")
    context.replace_text(irq_conf, "#option interval '10'", "option interval '10'")
