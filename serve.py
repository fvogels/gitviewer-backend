from flask import Flask, jsonify
import git
import os


app = Flask(__name__, static_folder='dist', static_url_path='')


REPOSITORY_ROOT = '../temp'

def get_repo():
    return git.Repo(REPOSITORY_ROOT)


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

    return list(path[1:] for path in find_files_recursively([REPOSITORY_ROOT], skip_git_dir))


def get_staging_area_files():
    repo = get_repo()
    index = repo.index
    return [path.split('/') for path, stage in index.entries]


def get_branches(repo):
    return {head.name: head.commit.hexsha for head in repo.heads}


def build_commit_graph(repo):
    graph = {}
    for commit in repo.iter_commits():
        graph[commit.hexsha] = [parent.hexsha for parent in commit.parents]
    return graph


def collect_repository_information():
    repo = get_repo()
    return {
        'branches': get_branches(repo),
        'commits': build_commit_graph(repo),
    }


@app.route('/api/v1/working-area')
def working_area():
    files = get_working_area_files()
    data = {
        'files': files
    }
    return jsonify(data)


@app.route('/api/v1/working-area/<path:path>')
def working_area_file(path):
    path_parts = path.split('/')
    with open(os.path.join(REPOSITORY_ROOT, *path_parts), 'r') as f:
        contents = f.read()
    data = {
        'path': path,
        'contents': contents
    }
    return jsonify(data)


@app.route('/api/v1/staging-area')
def staging_area():
    files = get_staging_area_files()
    data = {
        'files': files
    }
    return jsonify(data)


@app.route('/api/v1/staging-area/<path:path>')
def staging_area_file(path):
    def select_blob(pair):
        stage, blob = pair
        print(blob.path)
        return blob.path == path

    repo = get_repo()
    index = repo.index
    blob = next(index.iter_blobs(select_blob))[1]

    data = {
        'path': path,
        'contents': blob.data_stream.read().decode('utf-8'),
    }
    return jsonify(data)


@app.route('/api/v1/repository')
def repository():
    data = collect_repository_information()
    return jsonify(data)


@app.route('/api/v1/repository/commits/<hexsha>')
def commit(hexsha):
    repo = get_repo()
    commit = repo.commit(hexsha)
    print(dir(commit))
    data = {
        'author': commit.author.name,
        'message': commit.message,
        'parents': [parent.hexsha for parent in commit.parents],
        'date': str(commit.committed_datetime)
    }
    return jsonify(data)

app.run()
