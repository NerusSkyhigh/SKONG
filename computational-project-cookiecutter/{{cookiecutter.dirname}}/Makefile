pull-data:
	rsync -Pauvh "{{cookiecutter.username}}@{{cookiecutter.remote_server}}:{{cookiecutter.remote_folder}}/data/" \
				  "./data/" \
				  --stats --progress --delete

push-data:
	rsync -Pauvh "./data/" \
				  "{{cookiecutter.username}}@{{cookiecutter.remote_server}}:{{cookiecutter.remote_folder}}/data/" \
				  --stats --progress --delete