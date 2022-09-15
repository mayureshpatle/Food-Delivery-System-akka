from http import HTTPStatus
from threading import Thread
import requests

# concurrent testcase
# checking if concurrent /agentSignOut requests work correctly
# checking if concurret /agent/{agentId} requests work correctly

# NOTE: concurrent /agentSignIn & /requestOrder request are already used in previous testcases, 
# so not making dedicated testcases for them


# RESTAURANT SERVICE    : http://localhost:8080
# DELIVERY SERVICE      : http://localhost:8081
# WALLET SERVICE        : http://localhost:8082

def assureAllAgentSignOut():
    """required after renitializing delivery"""
    agents = [201, 202, 203]
    for agent in agents:
        # wait till status becomes signed-out
        while True:
            http_response = requests.get(f"http://localhost:8081/agent/{agent}")
            agent_status = http_response.json().get("status")
            if agent_status=="signed-out": break


# ----------------/agentSignOut requests ---------------- #

def t1(result):  # First concurrent signOut request

    # Agent 201 signs out
    http_response = requests.post(
        "http://localhost:8081/agentSignOut", json={"agentId":201})

    result["1"] = http_response


def t2(result):  # Second concurrent signOut request

    # Agent 202 signs out
    http_response = requests.post(
        "http://localhost:8081/agentSignOut", json={"agentId":202})

    result["2"] = http_response

def t3(result):  # Third concurrent signOut request

    # Agent 203 signs out
    http_response = requests.post(
        "http://localhost:8081/agentSignOut", json={"agentId":203})

    result["3"] = http_response


# ---------------- /agent/{agentId} requests ---------------- #

def t4(result): # First concurrent /agent/{agentId} request

    # get details of agent 201
    http_response = requests.get("http://localhost:8081/agent/201")

    result['1'] = http_response

def t5(result): # Second concurrent /agent/{agentId} request

    # get details of agent 202
    http_response = requests.get("http://localhost:8081/agent/202")

    result['2'] = http_response

def t6(result): # Third concurrent /agent/{agentId} request

    # get details of agent 203
    http_response = requests.get("http://localhost:8081/agent/203")

    result['3'] = http_response


def test():

    result = {}

    # Reinitialize Restaurant service
    http_response = requests.post("http://localhost:8080/reInitialize")

    # Reinitialize Delivery service
    http_response = requests.post("http://localhost:8081/reInitialize")

    assureAllAgentSignOut()


    # Reinitialize Wallet service
    http_response = requests.post("http://localhost:8082/reInitialize")

    # Agent 201 signs in
    http_response = requests.post(
        "http://localhost:8081/agentSignIn", json={"agentId": 201})

    if(http_response.status_code != HTTPStatus.CREATED):
        return 'Fail'

    # Agent 202 signs in
    http_response = requests.post(
        "http://localhost:8081/agentSignIn", json={"agentId": 202})

    if(http_response.status_code != HTTPStatus.CREATED):
        return 'Fail'

    # Agent 203 signs in
    http_response = requests.post(
        "http://localhost:8081/agentSignIn", json={"agentId": 203})

    if(http_response.status_code != HTTPStatus.CREATED):
        return 'Fail'

    ### Parallel Execution Begins ###
    thread1 = Thread(target=t4, kwargs={"result": result})
    thread2 = Thread(target=t5, kwargs={"result": result})
    thread3 = Thread(target=t6, kwargs={"result": result})

    thread1.start()
    thread2.start()
    thread3.start()

    thread1.join()
    thread2.join()
    thread3.join()

    ### Parallel Execution Ends ###

    status_code1 = result["1"].status_code
    agentId1 = result["1"].json().get("agentId")
    status1 = result["1"].json().get("status")

    status_code2 = result["2"].status_code
    agentId2 = result["2"].json().get("agentId")
    status2 = result["2"].json().get("status")

    status_code3 = result["3"].status_code
    agentId3 = result["3"].json().get("agentId")
    status3 = result["3"].json().get("status")

    # check status code
    if {status_code1, status_code2, status_code3} != {HTTPStatus.OK}:
        return "Fail"

    # check if correct agentId's were returned
    if (agentId1, agentId2, agentId3) != (201, 202, 203):
        return 'Fail'
    
    # check if all agents are available
    if {status1, status2, status3} != {"available"}:
        return "Fail"


     # Send concurrent signOut requests
    result = {}

    ### Parallel Execution Begins ###
    thread1 = Thread(target=t1, kwargs={"result": result})
    thread2 = Thread(target=t2, kwargs={"result": result})
    thread3 = Thread(target=t3, kwargs={"result": result})

    thread1.start()
    thread2.start()
    thread3.start()

    thread1.join()
    thread2.join()
    thread3.join()

    ### Parallel Execution Ends ###

    status_code1 = result["1"].status_code

    status_code2 = result["2"].status_code

    status_code3 = result["3"].status_code

    if {status_code1, status_code2, status_code3} != {HTTPStatus.CREATED}:
        return "Fail"
    
    
    # again send concurrent /agent/{agentId} requests to check if all agents were signed-out
    ### Parallel Execution Begins ###
    thread1 = Thread(target=t4, kwargs={"result": result})
    thread2 = Thread(target=t5, kwargs={"result": result})
    thread3 = Thread(target=t6, kwargs={"result": result})

    thread1.start()
    thread2.start()
    thread3.start()

    thread1.join()
    thread2.join()
    thread3.join()

    ### Parallel Execution Ends ###

    status_code1 = result["1"].status_code
    agentId1 = result["1"].json().get("agentId")
    status1 = result["1"].json().get("status")

    status_code2 = result["2"].status_code
    agentId2 = result["2"].json().get("agentId")
    status2 = result["2"].json().get("status")

    status_code3 = result["3"].status_code
    agentId3 = result["3"].json().get("agentId")
    status3 = result["3"].json().get("status")

    # check status code
    if {status_code1, status_code2, status_code3} != {HTTPStatus.OK}:
        return "Fail"

    # check if correct agentId's were returned
    if (agentId1, agentId2, agentId3) != (201, 202, 203):
        return 'Fail'
    
    # check if all agents are available
    if {status1, status2, status3} != {"signed-out"}:
        return "Fail"


    return 'Pass'


if __name__ == "__main__":

    print(test())
