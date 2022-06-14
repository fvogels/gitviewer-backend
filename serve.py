from flask import Flask, jsonify
import git
import os


app = Flask(__name__, static_folder='dist', static_url_path='')


def find_files_recursively(path, skip_predicate):
    for entry in os.scandir(os.path.join(*path)):
        if entry.is_dir():
            if not skip_predicate(entry.name):
                yield from find_files_recursively([*path, entry.name], skip_predicate)
        else:
            yield [*path, entry.name]


def get_working_area_files():
    def skip_git_dir(name):
        return name == '.git'

    return list(path[1:] for path in find_files_recursively(['../temp'], skip_git_dir))


def get_staging_area_files():
    repo = git.Repo('../temp')
    index = repo.index
    return [path.split('/') for path, stage in index.entries]


@app.route('/api/v1/working-area')
def working_area():
    files = get_working_area_files()
    data = {
        'files': files
    }
    return jsonify(data)


@app.route('/api/v1/staging-area')
def staging_area():
    files = get_staging_area_files()
    data = {
        'files': files
    }
    return jsonify(data)


app.run()