curl https://world.stevenamoore.dev/admin/dbdump > /dev/null
cp -f /root/prod/world-prod/app/dbbackups/* /root/dev/world-backend-dev/app/dbbackups/ > /dev/null
curl https://backenddev.world.stevenamoore.dev/admin/dbload > /dev/null
docker system prune -af > /dev/null