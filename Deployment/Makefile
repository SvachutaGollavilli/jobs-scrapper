.PHONY: deploy stop restart logs

deploy:
	./deploy.sh

stop:
	cd "Docker Files" && docker-compose down

restart:
	cd "Docker Files" && docker-compose restart

logs:
	cd "Docker Files" && docker-compose logs -f
