dirs=$(ls ./services)

for sub_dir in $dirs; do
    sudo docker-compose -f ./services/$sub_dir/docker-compose.yml down --volumes --remove-orphans
done

echo "All services stopped"
