from http import HTTPStatus
import requests

# sequential test case
# check whether deductBalance endpoint of 
# wallet microservice works correctly

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

def test():
    test_result = 'Pass'

    # Reinitialize Restaurant service
    http_response = requests.post("http://localhost:8082/reInitialize")

    if(http_response.status_code != HTTPStatus.CREATED):
        test_result = 'Fail'

    # Deduct 500 from the wallet of custId 301 
    http_response =requests.post(
        "http://localhost:8082/deductBalance", json = {"custId": 301, "amount": 500})

    if http_response.status_code != 201:
        test_result = 'Fail'

    # check whether the balance updated appropriately or not
    http_response =requests.get("http://localhost:8082/balance/301")

    res_body = http_response.json();
    if res_body.get("balance") != 1500:
        test_result = "Fail"

    # Deduct the balance greater than the balance present in the wallet of custId 301
    http_response =requests.post(
        "http://localhost:8082/deductBalance", json = {"custId": 301, "amount": 1600})

    if http_response.status_code != 410:
        test_result = 'Fail'


    # Check whether the balance remains same or not
    http_response =requests.get("http://localhost:8082/balance/301")

    res_body = http_response.json();
    if res_body.get("balance") != 1500:
        test_result = "Fail"

    return test_result


if __name__ == "__main__":
    test_result = test()
    print(test_result)
