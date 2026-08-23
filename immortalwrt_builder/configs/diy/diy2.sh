#!/bin/bash
#=================================================
# MZwrt script
#=================================================             



##配置IP
sed -i 's/192.168.1.1/192.168.10.1/g' package/base-files/files/bin/config_generate

##
rm -rf ./feeds/extraipk/theme/luci-theme-argon-18.06
rm -rf ./feeds/extraipk/theme/luci-app-argon-config-18.06
rm -rf ./feeds/extraipk/theme/luci-theme-design
rm -rf ./feeds/extraipk/theme/luci-theme-edge
rm -rf ./feeds/extraipk/theme/luci-theme-ifit
rm -rf ./feeds/extraipk/theme/luci-theme-opentopd
rm -rf ./feeds/extraipk/theme/luci-theme-neobird

rm -rf ./package/feeds/extraipk/luci-theme-argon-18.06
rm -rf ./package/feeds/extraipk/luci-app-argon-config-18.06
rm -rf ./package/feeds/extraipk/theme/luci-theme-design
rm -rf ./package/feeds/extraipk/theme/luci-theme-edge
rm -rf ./package/feeds/extraipk/theme/luci-theme-ifit
rm -rf ./package/feeds/extraipk/theme/luci-theme-opentopd
rm -rf ./package/feeds/extraipk/theme/luci-theme-neobird

##取消安装usbprinter和samba4

sed -i "s/luci-app-samba4//g" target/linux/mediatek/image/mt7981.mk
sed -i "s/luci-app-usb-printer//g" target/linux/mediatek/image/mt7981.mk
sed -i "s/luci-i18n-usb-printer-zh-cn//g" target/linux/mediatek/image/mt7981.mk

##取消bootstrap为默认主题
sed -i '/set luci.main.mediaurlbase=\/luci-static\/bootstrap/d' feeds/luci/themes/luci-theme-bootstrap/root/etc/uci-defaults/30_luci-theme-bootstrap
sed -i 's/luci-theme-bootstrap/luci-theme-argon/g' feeds/luci/collections/luci/Makefile
sed -i 's/luci-theme-bootstrap/luci-theme-argon/g' feeds/luci/collections/luci-nginx/Makefile

##更改主机名
sed -i "s/hostname='.*'/hostname='uluaWrt'/g" package/base-files/files/bin/config_generate

##加入作者信息
sed -i "s/DISTRIB_DESCRIPTION='*.*'/DISTRIB_DESCRIPTION='uluaWrt-$(date +%Y%m%d)'/g"  package/base-files/files/etc/openwrt_release
sed -i "s/DISTRIB_REVISION='*.*'/DISTRIB_REVISION=' By ulua'/g" package/base-files/files/etc/openwrt_release
# cp -af feeds/extraipk/patch/diy/banner-MZwrt  package/base-files/files/etc/banner

# sed -i "2iuci set istore.istore.channel='MZ_wrt'" package/emortal/default-settings/files/99-default-settings
# sed -i "3iuci commit istore" package/emortal/default-settings/files/99-default-settings
# sed -i.bak "s,mirrors.vsean.net/openwrt,mirrors.vsean.net/openwrt,g" package/emortal/default-settings/files/99-default-settings


##WiFi
sed -i "s/MT7981_AX3000_2.4G/uluaWrt-2.4G/g" package/mtk/drivers/wifi-profile/files/mt7981/mt7981.dbdc.b0.dat
sed -i "s/MT7981_AX3000_5G/uluaWrt-5G/g" package/mtk/drivers/wifi-profile/files/mt7981/mt7981.dbdc.b1.dat

##New WiFi
sed -i "s/ImmortalWrt-2.4G/uluaWrt-2.4G/g" package/mtk/applications/mtwifi-cfg/files/mtwifi.sh
sed -i "s/ImmortalWrt-5G/uluaWrt-5G/g" package/mtk/applications/mtwifi-cfg/files/mtwifi.sh

# ttyd ssl
cat <<EOL >> package/feeds/packages/ttyd/files/ttyd.config
	option ssl '1'
	option ssl_cert '/etc/nginx/conf.d/_lan.crt'
	option ssl_key '/etc/nginx/conf.d/_lan.key'
EOL
# luci argon config
cat <<EOL > package/feeds/luci/luci-app-argon-config/root/etc/config/argon
config global
	option primary '#5e72e4'
	option dark_primary '#483d8b'
	option mode 'normal'
	option online_wallpaper 'none'
	option transparency '0.5'
	option blur '10'
	option blur_dark '10'
	option transparency_dark '0.5'
EOL

# statistics disable wireless collect
sed -z -i "s/config statistics 'collectd_iwinfo'\n\toption enable '1'/config statistics 'collectd_iwinfo'\n\toption enable '0'/g" package/feeds/luci/luci-app-statistics/root/etc/config/luci_statistics
# statistics disable interface collect
sed -z -i "s/config statistics 'collectd_interface'\n\toption enable '1'/config statistics 'collectd_interface'\n\toption enable '0'/g" package/feeds/luci/luci-app-statistics/root/etc/config/luci_statistics
