.PHONY: help install run test docker

help:
	@echo "make install - Install dependencies"
	@echo "make run     - Run application"
	@echo "make docker  - Run with Docker"

install:
	python3 setup.py

run:
	python3 run.py

docker:
	cd "Docker Files" && docker-compose up -d

stop:
	cd "Docker Files" && docker-compose down
