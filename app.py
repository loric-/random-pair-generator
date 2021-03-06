from flask import Flask, render_template, request, redirect, url_for
import os
import random
import config
import translate
import db
import auth
import gif

app = Flask(__name__)
#app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.route("/")
def index():
    pairs = []
    pairs_db = db.get_pairs()
    for pair in pairs_db:
        pairs.append({
            'first': db.get_item(pair.get('first')),
            'second': db.get_item(pair.get('second'))
        })

    return render_template(
        'index.html',
        has_pairs=db.has_pairs(),
        config=db.get_config(),
        items=db.get_items(),
        pairs=pairs
    )

@app.route("/edit", methods=['POST', 'GET'])
@auth.requires_auth
def edit():
    if request.method == 'POST':
        filename = None

        # Save file
        if 'photo' in request.files:
            file = request.files['photo']
            filename = file.filename
            file.save(config.upload_dir(filename))

        # Add item
        db.add_item(request.form['name'], filename)

    return render_template('edit.html', items=db.get_items())

@app.route('/remove/<id>')
@auth.requires_auth
def remove(id):
    db.remove_item(id)
    return redirect(url_for('edit'))

@app.route("/run", methods=['POST', 'GET'])
@auth.requires_auth
def run():
    if request.method == 'POST':
        db.set_message_before(request.form['message-before'])
        db.set_message_after(request.form['message-after'])
    return render_template('run.html', config=db.get_config(), has_pairs=db.has_pairs())

@app.route('/generate')
@auth.requires_auth
def generate():
    db.reset_pairs()

    # Generate list of id
    items = []
    for item in db.get_items():
        items.append(str(item.get('_id')))

    # Fill in with None if list not odd
    if len(items) % 2 != 0:
        items.append(None)

    # Shuffle
    random.shuffle(items)

    # Generate pairs
    it = iter(items)
    pairs = list(zip(it, it))

    # Add pairs
    for pair in pairs:
        db.add_pair({'first': pair[0], 'second': pair[1]})

    # Generate gif
    gif.generate()
    return redirect(url_for('run'))

@app.route('/reset')
@auth.requires_auth
def reset():
    db.reset_pairs()
    gif.remove()
    return redirect(url_for('run'))

@app.template_filter('upload_dir')
def prepend_upload_path(filename):
    return url_for('static', filename=os.path.join('upload', filename))

@app.template_filter('translate')
def find_translation(label):
    return translate.get_value(label)

if __name__ == "__main__":
    #app.run(host='0.0.0.0', port=80, debug=True)
    app.run(host='0.0.0.0', port=80)
