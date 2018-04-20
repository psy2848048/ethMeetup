import web3

from web3 import Web3, HTTPProvider
from web3.contract import Contract, ConciseContract
from solc import compile_source

from flask import Flask, session, request, g, make_response, json
from flask_cors import CORS
import pymysql

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": "true"}})

contract_source = """
pragma solidity ^0.4.8;

contract  MLCoin {
    // (1) 상태 변수 선언
    string public name; // 토큰 이름
    string public symbol; // 토큰 단위
    uint8 public decimals; // 소수점 이하 자릿수
    uint256 public totalSupply; // 토큰 총량
    mapping (address => uint256) public balanceOf; // 각 주소의 잔고
    mapping (address => bool) public blackList; // 블랙리스트

    // (3) 이벤트 알림
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Blacklisted(address indexed target);
    event DeleteFromBlacklist(address indexed target);
    event RejectedPaymentToBlacklistedAddr(address indexed from, address indexed to, uint256 value);
    event RejectedPaymentFromBlacklistedAddr(address indexed from, address indexed to, uint256 value);
    event Cashback(address indexed from, address indexed to, uint256 value);

    // (4) 생성자
    function MLCoin(uint256 _supply, string _name, string _symbol, uint8 _decimals) public {
        balanceOf[msg.sender] = _supply;
        name = _name;
        symbol = _symbol;
        decimals = _decimals;
        totalSupply = _supply;
    }   
    
    function transfer(address _to, uint256 _value) public {
        // 부정 송금 확인
        if (balanceOf[msg.sender] < _value) revert();
        if (balanceOf[_to] + _value < balanceOf[_to]) revert();

        balanceOf[msg.sender] -= _value;
        balanceOf[_to] += _value;
    }

    function burnToken(uint256 _value) public {
        if (balanceOf[msg.sender] < _value) revert();

        totalSupply -= _value;
        balanceOf[msg.sender] -= _value;
    }
}

"""

#inst.functions.totalSupply().call()

def getInstance():
    compiled_sol = compile_source(contract_source)
    contract_interface = compiled_sol['<stdin>:MLCoin']
    w3 = Web3(HTTPProvider('http://14.39.173.205:8545'))
    w3.personal.unlockAccount(w3.personal.listAccounts[0], 'pass0')
    w3.personal.unlockAccount(w3.personal.listAccounts[1], 'pass1')
    contract_instance = w3.eth.contract(Web3.toChecksumAddress("0xf88129dd6a352ed1e3bfcef8f5bee886b3184645"),
                                        abi=contract_interface['abi']
                        )

    return contract_instance

def emitco2(value):
    inst = getInstance()
    w3 = Web3(HTTPProvider('http://14.39.173.205:8545'))
    print(w3.personal.listAccounts)
    res = inst.functions.burnToken(value).transact({
          'from': Web3.toChecksumAddress(w3.personal.listAccounts[0])
        , 'gas': 150000
        , 'gasPrice': w3.toWei('15', 'gwei')
        })

@app.before_request
def before_request():
    """ 
    모든 API 실행 전 실행하는 부분
    """
    # DB 접속
    g.db = pymysql.connect(
             host="hotelchat.ce2zgalnsfar.ap-northeast-2.rds.amazonaws.com",
             user="hotelchat",
             password="noSecret01!",
             db="hacker",
             charset='utf8',
             cursorclass=pymysql.cursors.DictCursor
            )  

@app.route('/api/v1/emitco2', methods=["POST"])
def emitco2API():
    cursor = g.db.cursor()
    consumerAddress = request.form['consumerAddress']
    consumingType = request.form['consumingType']
    producerAddress = request.form['producerAddress']
    consumeAmount = request.form['consumeAmount']
    produceType = request.form['produceType']
    produceAmount = request.form['produceAmount']

    consumeAmount = int(consumeAmount)
    produceAmount = int(produceAmount)

    co2emissionAmount = produceAmount * 1
    consumedToken = co2emissionAmount * 2

    emitco2(consumedToken)

    query = """
        INSERT INTO transaction
          (consumerAddress, consumingType, producerAddress, consumeAmount, produceType, produceAmount, co2emissionAmount, consumedToken)
        VALUES
          (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (consumerAddress, consumingType, producerAddress, consumeAmount,
        produceType, produceAmount, co2emissionAmount, consumedToken))
    g.db.commit()

    return make_response(json.jsonify(result="OK"), 200)

@app.route('/api/v1/totalsupply', methods=["GET"])
def getTotal():
    inst = getInstance()
    totalSupply = inst.functions.totalSupply().call()
    return make_response(json.jsonify(total=totalSupply), 200)

@app.route('/api/v1/mytoken', methods=["GET"])
def getMine():
    inst = getInstance()
    totalSupply = inst.functions.totalSupply().call()
    return make_response(json.jsonify(total=totalSupply), 200)

@app.route('/api/v1/transactions', methods=["GET"])
def getAllTransactions():
    cursor = g.db.cursor()
    query = """
        SELECT 
          consumerAddress, consumingType, producerAddress, consumeAmount, produceType, produceAmount, co2emissionAmount, consumedToken
        FROM transaction
        ORDER BY id ASC
    """
    cursor.execute(query)
    res = cursor.fetchall()
    return make_response(json.jsonify(res), 200)

if __name__ == "__main__":
    from gevent.wsgi import WSGIServer

    https = WSGIServer(('0.0.0.0', 5000), app)
    https.serve_forever()
