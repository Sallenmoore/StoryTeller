curl https://world.stevenamoore.dev/api/admin/dbdump
cp -f /root/prod/world-prod/api/dbbackups/* /root/dev/world-dev/api/dbbackups/
curl https://dev.world.stevenamoore.dev/api/admin/dbload