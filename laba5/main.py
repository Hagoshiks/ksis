from flask import Flask, request, jsonify, send_file, abort, render_template
import os
import shutil
from datetime import datetime
app = Flask(__name__)
BASE_DIR = os.path.abspath('storage')
size = 0
def get_filesystem_path(path):
    fs_path = os.path.abspath(os.path.join(BASE_DIR, path))
    if not fs_path.startswith(BASE_DIR):
        return None
    return fs_path


@app.route('/', defaults={'path': ''}, methods=['PUT', 'GET', 'DELETE', 'HEAD'])
@app.route('/<path:path>', methods=['PUT', 'GET', 'DELETE', 'HEAD'])
def handle_request(path):
    fs_path = get_filesystem_path(path)
    if not fs_path:
        abort(403)

    # if request.method == 'PUT':
    #     dir_path = os.path.dirname(fs_path)
    #     os.makedirs(dir_path, exist_ok=True)
    #     with open(fs_path, 'wb') as f:
    #         f.write(request.get_data())
    #     return '', 201
    if request.method == 'PUT':
        dir_path = os.path.dirname(fs_path)
        os.makedirs(dir_path, exist_ok=True)
        data = request.get_data()  # Получаем данные
        if not data:
            return 'No data provided', 400  # Проверка на пустые данные
        with open(fs_path, 'wb') as f:
            f.write(data)
        return '', 201

    elif request.method == 'GET':
        if os.path.isdir(fs_path):
            try:
                entries = os.listdir(fs_path)
                file_list = []
                current_path = path.rstrip('/')

                for entry in entries:
                    entry_path = os.path.join(fs_path, entry)
                    is_dir = os.path.isdir(entry_path)
                    stat = os.stat(entry_path)
                    item_url = f"{entry}" if current_path else entry
                    if is_dir:
                        item_url += "/"

                    file_list.append({
                        'name': entry,
                        'size': stat.st_size,
                        'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'is_directory': is_dir,
                        'url': item_url
                    })
                # Отдаем HTML или JSON в зависимости от заголовка Accept
                if 'text/html' in request.headers.get('Accept', ''):
                    return render_template('directory.html', path=f'/{path}' if path else '/', items=file_list)
                return jsonify(file_list)
            except FileNotFoundError:
                abort(404)
        elif os.path.isfile(fs_path):
            return send_file(fs_path)
        else:
            abort(404)

    elif request.method == 'HEAD':

        if os.path.isfile(fs_path):
            stat = os.stat(fs_path)
            headers = {
                'Content-Length': str(stat.st_size),
                'Last-Modified': datetime.fromtimestamp(stat.st_mtime).strftime('%a, %d %b %Y %H:%M:%S')
            }
            with open(fs_path, 'r', encoding='utf-8') as file:
                content = file.read()  # Весь текст файла сохраняется в переменную content
                
            response = app.make_response((content, 200, headers))
            response.headers.remove('Server')
            response.headers.remove('Date')
            response.headers.remove('Content-Type')
            response.headers.remove('Connection')
            return response
            # return ('', 200, headers)
        else:
            abort(404)

    elif request.method == 'DELETE':
        if not os.path.exists(fs_path):
            abort(404)
        if os.path.isfile(fs_path):
            os.remove(fs_path)
        else:
            shutil.rmtree(fs_path)
        return '', 204

    else:
        abort(405)

if __name__ == '__main__':
    os.makedirs(BASE_DIR, exist_ok=True)
    app.run(debug=True, extra_files=[BASE_DIR])  # Следит за изменениями файлов
