from logging import debug
from flask import Flask, jsonify, request
from flask_cors import CORS
# from flask_jwt_extended import create_access_token, jwt_required, JWTManager,
import pandas as pd
import numpy as np
from main import scrape # scrape(domains) -- domains foramt is [['domain.com', 'server']]


app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
# CORS(app)

# @app.route('/', methods=['GET'])
# def hello():
#     return jsonify({'msg' : 'welcome'})

@app.route('/api/scrape', methods=['GET', 'POST'])
def scrape_domain():
    if request.method == 'POST' and request.headers['App-Access'] == 'true':
        data = request.json
 
        input_data = [[data['domain'], 'none']]
        scrape_domain = scrape(input_data)
        print(type(scrape_domain))
        if type(scrape_domain) == str:
            return jsonify('Error')
        # scrape_domain = pd.read_csv('esweetman.csv')
        else:
            scrape_domain = scrape_domain.drop([0])
            # scrape_domain = scrape_domain.loc[:, ~scrape_domain.columns.str.contains('^Unnamed')]
            # print(scrape_domain)
            scrape_domain = scrape_domain.applymap(str)
            scrape_domain = scrape_domain.to_json(orient="records")
            # print(scrape_domain)
            return scrape_domain
            # return jsonify({'msg': 'true'})

    else:
        return "Error"


if __name__ == '__main__':
    app.run(debug=True)