from flask import Flask, render_template, request
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        # Construct the XML content
        xml_content = construct_xml(request.form)
        user_id = request.form.get('user_id', 'user_configuration')

        # Define the file path
        file_path = os.path.join('example_sims', 'users', f'{user_id}.xml')

        # Store the XML content in the specified directory
        with open(file_path, 'w') as file:
            file.write(xml_content)

        # After storing the file, you can redirect or inform the user of success
        # For simplicity, let's just return a simple confirmation message
        return f"Configuration for {user_id} saved successfully."

    return render_template('form.html')

def construct_xml(form_data):
    # Placeholder function to construct XML from form data
    # You should implement XML construction based on your specific requirements
    return "<userConfiguration></userConfiguration>"

if __name__ == '__main__':
    app.run(debug=True)