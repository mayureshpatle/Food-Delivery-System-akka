from http import HTTPStatus
import requests

# sequential test case
# try /acceptOrder for more than available quantity
# validate by sending another request with bottleneck quantity

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
    http_response = requests.post("http://localhost:8080/reInitialize")

    if(http_response.status_code != HTTPStatus.CREATED):
        test_result = 'Fail'

    # request restId 102 with itemId 1 and qty 20
    http_response =requests.post(
        "http://localhost:8080/acceptOrder", json = {"restId": 102, "itemId": 1, "qty":  20})

    if http_response.status_code != 410:
        test_result = 'Fail'

    # request restId 102 with itemId 1 and qty 10
    http_response =requests.post(
        "http://localhost:8080/acceptOrder", json = {"restId": 102, "itemId": 1, "qty":  10})

    if http_response.status_code != 201:
        test_result = 'Fail'


    return test_result


if __name__ == "__main__":
    test_result = test()
    print(test_result)
